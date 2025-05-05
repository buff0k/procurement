# Copyright (c) 2025, Isambane Mining (Pty) Ltd
# For license information, please see license.txt

import frappe
from frappe import _

def get_context(context):
    if not frappe.session.user:
        frappe.throw(_("You must be logged in to access this page."), frappe.PermissionError)

    # Fetch Supplier linked to this user
    supplier = frappe.db.get_value("Supplier", {"portal_users.user": frappe.session.user}, "name")

    if not supplier:
        frappe.throw(_("You do not have permission to access RFQs."), frappe.PermissionError)

    # Get RFQs this supplier is allowed to see
    rfqs = frappe.get_all(
        "Request for Quotation",
        filters={"docstatus": ["<", 2]},
        fields=["name", "status", "transaction_date"],
        order_by="creation desc"
    )

    for rfq in rfqs:
        rfq["items"] = frappe.get_all(
            "Request for Quotation Item",
            filters={"parent": rfq.name},
            fields=["item_name"]
        )

    context.rfqs = rfqs
    return context
