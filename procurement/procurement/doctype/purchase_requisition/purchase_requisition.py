# Copyright (c) 2024, Isambane Mining (Pty) Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


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