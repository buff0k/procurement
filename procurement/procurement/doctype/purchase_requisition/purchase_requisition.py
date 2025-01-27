# Copyright (c) 2024, Isambane Mining (Pty) Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import add_days, today

class PurchaseRequisition(Document):
	pass

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
        # Set any additional fields that don't directly map
        target.cost_center = source.cost_center  # Assuming 'location' maps to 'cost_center'
        
        # Calculate the schedule date to be one week in the future
        schedule_date = add_days(today(), 7)
        
        # Default UOM (assuming "Nos" exists in UOM DocType)
        default_uom = frappe.db.get_value('UOM', {'uom_name': 'Nos'}, 'name')
        
        for item in target.items:
            item.schedule_date = schedule_date
            item.uom = default_uom

    # Map fields from Purchase Requisition to Purchase Order
    doclist = get_mapped_doc("Purchase Requisition", source_name, {
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
    }, target_doc, set_missing_values)

    return doclist