import frappe
from frappe import _
from frappe.utils import formatdate

def get_context(context):
    context.no_cache = 1
    context.show_sidebar = True

    # Load the Supplier Quotation document
    context.doc = frappe.get_doc("Supplier Quotation", frappe.form_dict.name)

    # Ensure the current user is the supplier for the quotation
    supplier = context.doc.supplier
    unauthorized_user(supplier)

    # Add supplier-specific details
    update_supplier_details(context)

    # Get all UOMs from the UOM DocType
    context.uoms = frappe.get_all("UOM", fields=["name"])

    # Expose quotation_number explicitly for the template (though context.doc.quotation_number is also available)
    context.quotation_number = context.doc.quotation_number

    # CSRF token
    context["csrf_token"] = frappe.local.session.data.csrf_token

    # Pass items to the template
    context["quotation_items"] = context.doc.items

    # Pass custom attachments
    context["custom_attachments"] = [{
        "file_url": attachment.file_url,
        "description": attachment.description
    } for attachment in context.doc.custom_attachments]

    # Title for the page
    context["title"] = context.doc.name

    # Safety check for missing item_code
    for item in context.doc.items:
        if not item.item_code:
            frappe.throw(_("Item code missing for item in Supplier Quotation: {0}").format(item.idx))

def unauthorized_user(supplier):
    # Check if the current user is linked to the supplier
    if not check_supplier_has_docname_access(supplier):
        frappe.throw(_("You are not authorized to view this Supplier Quotation."), frappe.PermissionError)

def check_supplier_has_docname_access(supplier):
    # Query to check if the current user is linked to this supplier in the portal_users table
    status = False
    if frappe.db.exists("Supplier", supplier):
        # Check if the user is in the portal_users field linked to the supplier
        status = frappe.db.exists(
            "Portal User",
            {
                "parent": supplier, 
                "user": frappe.session.user
            }
        )
    return status

def update_supplier_details(context):
    supplier_doc = frappe.get_doc("Supplier", context.doc.supplier)
    context.doc.currency = supplier_doc.default_currency or frappe.get_cached_value(
        "Company", context.doc.company, "default_currency"
    )
    context.doc.currency_symbol = frappe.db.get_value("Currency", context.doc.currency, "symbol", cache=True)
    context.doc.number_format = frappe.db.get_value(
        "Currency", context.doc.currency, "number_format", cache=True
    )
    context.doc.buying_price_list = supplier_doc.default_price_list or ""
