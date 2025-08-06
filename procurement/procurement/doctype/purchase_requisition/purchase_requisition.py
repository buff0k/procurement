# Copyright (c) 2025, Isambane Mining (Pty) Ltd and contributors
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

    # Check if the site_code field has been populated
    if not doc.site_code:
        frappe.throw(_("Site is required before generating an order number."))

    # Check if the official_company_order_no is already populated
    if doc.official_company_order_no:
        frappe.throw(_("Order Number has already been generated and cannot be changed."))

    # Generate the order number components
    current_date = getdate(nowdate())
    year_last_two_digits = str(current_date.year)[-2:]
    month_abbr = current_date.strftime("%b").upper()  # First three letters of the month
    date_two_digits = current_date.strftime("%d")  # Day of the month as two digits
    company_abbr = doc.company_abbr  # Assuming company_abbr is a field in the doctype
    pr_number = doc.pr_number  # Assuming pr_number is a field in the doctype
    site_code = doc.site_code  # Assuming site_code is a field in the doctype

    # Generate the sequence number for the order
    sequence_number = get_next_sequence_number(year_last_two_digits, month_abbr, site_code)

    # Construct the order number
    order_number = f"{year_last_two_digits}{month_abbr}{date_two_digits}{company_abbr}{sequence_number:03d}/{site_code}"

    # Update the official_company_order_no field
    doc.official_company_order_no = order_number
    doc.save()

    frappe.msgprint(_("Order Number generated successfully: {0}").format(order_number))

def get_next_sequence_number(year_last_two_digits, month_abbr, site_code):
    # Construct the key for the sequence
    sequence_key = f"{year_last_two_digits}{month_abbr}%/{site_code}"

    # Get the last sequence number used for this key
    last_sequence = frappe.db.sql("""
        SELECT official_company_order_no 
        FROM `tabPurchase Requisition` 
        WHERE official_company_order_no LIKE %s
        ORDER BY creation DESC 
        LIMIT 1
    """, (sequence_key,), as_dict=True)

    if last_sequence:
        last_order_number = last_sequence[0]["official_company_order_no"]
        frappe.logger().info(f"Last Order Found: {last_order_number}")

        # Extract the numeric sequence portion
        try:
            # Extracts the number before "/SITE"
            sequence_part = int(last_order_number.split("/")[0][-3:])
            next_sequence_number = sequence_part + 1
        except (IndexError, ValueError):
            next_sequence_number = 1  # If extraction fails, default to 001
    else:
        next_sequence_number = 1  # Start from 001 if no previous order exists

    frappe.logger().info(f"Next Sequence Number: {next_sequence_number}")
    return next_sequence_number

@frappe.whitelist()
def validate_before_submit(doc, method):
    if not doc.invoice_received or not doc.grn_completed:
        frappe.throw(_("You cannot submit this Purchase Requisition unless both 'Invoice Received' and 'GRN Completed' are checked."))

@frappe.whitelist()
def get_buyer_for_site(site_code):
    # Get Buyer Site Allocation records
    allocations = frappe.get_all("Buyer Site Allocation", fields=["name", "buyer"])

    for allocation in allocations:
        # Check if site_code exists in the child table
        child_sites = frappe.get_all("Site Code List", 
                                     filters={"parent": allocation.name, "site_code": site_code}, 
                                     fields=["site_code"])
        if child_sites:
            return allocation.buyer  # Return the first matching buyer

    return None  # No matching allocation found
