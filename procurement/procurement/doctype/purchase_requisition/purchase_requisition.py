# Copyright (c) 2024, Isambane Mining (Pty) Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import add_days, today, nowdate, getdate
from frappe import _

class PurchaseRequisition(Document):
	pass

@frappe.whitelist()
def get_company_details(company=None):
    """Fetches default_letter_head and company_abbr based on the selected company."""
    if not company:
        # Fetch the default company from Global Defaults
        company = frappe.db.get_single_value("Global Defaults", "default_company")
        if not company:
            frappe.throw("Default company is not set in Global Defaults.")

    # Get the default_letter_head from the Company DocType
    default_letter_head = frappe.db.get_value("Company", company, "default_letter_head")

    # Get the company_abbr (document name is the same as the value of company_abbr)
    company_abbr = frappe.db.get_value(
        "Company Abbreviations",
        {"company": company},
        "company_abbr"
    )

    if not company_abbr:
        frappe.throw(f"No abbreviation found for the company: {company}")

    return {
        "default_letter_head": default_letter_head,
        "company_abbr": company_abbr,  # This is the document name as well
    }

@frappe.whitelist()
def update_employee_names(doc, method):
    # Helper function to get employee name from Employee DocType
    def get_employee_name(employee_id):
        employee = frappe.get_doc("Employee", employee_id)
        return employee.employee_name if employee else ""

    # Update the read-only fields based on linked Employee documents
    doc.req_name = get_employee_name(doc.requested_by)
    doc.del_name = get_employee_name(doc.deliver_to)
    doc.auth_name = get_employee_name(doc.authorized_by)
    
    # Save the updated document
    doc.save()

# Trigger the update on document save
@frappe.whitelist()
def on_update(doc, method):
    update_employee_names(doc, method)

@frappe.whitelist()
def make_purchase_order(source_name, target_doc=None):
    def set_missing_values(source, target):
        # Set additional fields
        target.cost_center = source.account  # Assuming 'account' maps to 'cost_center'
        
        # Calculate the schedule date to be one week in the future
        schedule_date = add_days(today(), 7)
        
        # Default UOM (assuming "Nos" exists in UOM DocType)
        default_uom = frappe.db.get_value('UOM', {'uom_name': 'Nos'}, 'name')
        
        for item in target.items:
            item.schedule_date = schedule_date
            item.uom = default_uom

    # Map fields from Purchase Requisition to Purchase Order
    doclist = get_mapped_doc(
        "Purchase Requisition",
        source_name,
        {
            "Purchase Requisition": {
                "doctype": "Purchase Order",
                "field_map": {
                    "name": "purchase_requisition",  # Link the Purchase Requisition to the Purchase Order
                    "company": "company",
                    "supplier": "supplier"
                }
            },
            "Purchase Requisition List": {
                "doctype": "Purchase Order Item",
                "field_map": {
                    "item": "item_code",
                    "qty": "qty",
                    "unit_price": "rate"
                },
                "condition": lambda doc: doc.item  # Skip rows where item is not set
            }
        },
        target_doc,
        set_missing_values
    )

    # Explicitly set the name of the Purchase Order
    purchase_order_name = source_name

    # Check if a Purchase Order with the same name already exists
    if frappe.db.exists("Purchase Order", purchase_order_name):
        frappe.throw(_("A Purchase Order with the name {0} already exists").format(purchase_order_name))

    # Bypass the naming series and insert the document with the specified name
    doclist.name = purchase_order_name
    doclist.flags.ignore_permissions = True  # Ensure permissions don't block the save
    doclist.insert(ignore_permissions=True)  # Insert the document directly into the database

    return doclist

@frappe.whitelist()
def generate_order_number(doc):
    # Load the document
    doc = frappe.get_doc("Purchase Requisition", doc)

    # Check if the official_company_order_no is already populated
    if doc.official_company_order_no:
        frappe.throw(_("Order Number has already been generated and cannot be changed."))

    # Generate the order number
    current_date = getdate(nowdate())
    year_last_two_digits = str(current_date.year)[-2:]
    month_abbr = current_date.strftime("%b").upper()  # First three letters of the month
    company_abbr = doc.company_abbr  # Assuming company_abbr is a field in the doctype
    pr_number = doc.pr_number  # Assuming pr_number is a field in the doctype
    site_code = doc.site_code  # Assuming site_code is a field in the doctype

    # Construct the order number
    order_number = f"{year_last_two_digits}{company_abbr}{month_abbr}{pr_number}/{site_code}"

    # Update the official_company_order_no field
    doc.official_company_order_no = order_number
    doc.save()

    frappe.msgprint(_("Order Number generated successfully: {0}").format(order_number))