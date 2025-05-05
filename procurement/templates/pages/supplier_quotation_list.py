# Copyright (c) 2025, Isambane Mining (Pty) Ltd
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import formatdate, get_number_format_info

def get_context(context):
    context.no_cache = 1
    context.title = _("My Supplier Quotations")
    context.show_sidebar = True

    supplier = get_supplier_for_user(frappe.session.user)
    if not supplier:
        frappe.throw(_("You are not authorized to view Supplier Quotations."), frappe.PermissionError)

    quotations = frappe.get_all(
        "Supplier Quotation",
        filters={"supplier": supplier},
        fields=["name", "quotation_number", "transaction_date", "status", "grand_total", "currency"],
        order_by="modified desc"
    )

    # Add item_name list for each quotation
    for q in quotations:
        q.currency_symbol = frappe.db.get_value("Currency", q.currency, "symbol") or q.currency
        q["items"] = frappe.get_all(
            "Supplier Quotation Item",
            filters={"parent": q.name},
            fields=["item_name"]
        )

    context.supplier_quotations = quotations

def get_supplier_for_user(user):
    result = frappe.get_all(
        "Portal User",
        filters={"user": user},
        fields=["parent"]
    )
    return result[0].parent if result else None

def enforce_supplier_permission(supplier):
    if not is_portal_user(supplier):
        frappe.throw(_("You are not authorized to view this Supplier Quotation."), frappe.PermissionError)

def is_portal_user(supplier):
    if not frappe.db.exists("Supplier", supplier):
        return False
    return frappe.db.exists(
        "Portal User",
        {
            "parent": supplier,
            "user": frappe.session.user
        }
    )

def enrich_supplier_context(context):
    supplier_doc = frappe.get_doc("Supplier", context.doc.supplier)
    context.doc.currency = supplier_doc.default_currency or frappe.get_cached_value(
        "Company", context.doc.company, "default_currency"
    )
    context.doc.currency_symbol = frappe.db.get_value("Currency", context.doc.currency, "symbol", cache=True)
    context.doc.number_format = frappe.db.get_value("Currency", context.doc.currency, "number_format", cache=True)
    context.doc.buying_price_list = supplier_doc.default_price_list or ""
