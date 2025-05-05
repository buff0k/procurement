# Copyright (c) 2025, Isambane Mining (Pty) Ltd
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today

def get_context(context):
    context.no_cache = 1
    context.title = _("My Requests for Quotation")
    context.show_sidebar = True

    supplier = get_supplier_for_user(frappe.session.user)
    if not supplier:
        frappe.throw(_("You are not authorized to view RFQs."), frappe.PermissionError)

    rfqs = frappe.get_all(
        "Request for Quotation",
        filters={
            "supplier": supplier,
            "docstatus": 1,
            "status": ["!=", "Cancelled"],
            "schedule_date": [">=", today()]
    },
        fields=["name", "transaction_date", "status"],
        order_by="`tabRequest for Quotation`.modified desc"
    )

    for rfq in rfqs:
        rfq["items"] = frappe.get_all(
            "Request for Quotation Item",
            filters={"parent": rfq.name},
            fields=["item_name"]
        )

    context.rfqs = rfqs

def get_supplier_for_user(user):
    result = frappe.get_all(
        "Portal User",
        filters={"user": user},
        fields=["parent"]
    )
    return result[0].parent if result else None
