import frappe
import json
from frappe.utils.file_manager import get_file, save_file
from werkzeug.wrappers import Response
from frappe import _

@frappe.whitelist(allow_guest=True)
def get_rfq_image(file_url):
    """Serves private RFQ images directly as a binary response"""

    # Strip extra query parameters like ?fid=...
    if "?" in file_url:
        file_url = file_url.split("?")[0]

    # Ensure only valid private file paths are processed
    if not file_url.startswith("/private/files/"):
        frappe.throw("Invalid file path")

    # Fetch only the file attached to an RFQ (ignore email attachments)
    file_doc = frappe.db.get_value(
        "File", 
        {"file_url": file_url, "attached_to_doctype": "Request for Quotation"}, 
        ["name", "attached_to_doctype", "attached_to_name"], 
        as_dict=True
    )

    # If no matching file is found, deny access
    if not file_doc:
        frappe.throw("Unauthorized access")

    # Read file content in binary mode
    file_path = frappe.get_site_path("private", "files", file_url.split("/")[-1])
    with open(file_path, "rb") as f:
        file_content = f.read()

    # Determine MIME type based on file extension
    file_extension = file_url.split('.')[-1].lower()
    mime_types = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "svg": "image/svg+xml"
    }
    content_type = mime_types.get(file_extension, "application/octet-stream")

    # Return the image as an HTTP response with correct headers
    response = Response(file_content, content_type=content_type)
    response.headers["Content-Disposition"] = f"inline; filename={file_url.split('/')[-1]}"
    return response

def get_supplier_quotations():
    user = frappe.session.user

    # Get linked supplier
    supplier = frappe.db.get_value("Supplier Portal User", {"user": user}, "parent")
    if not supplier:
        return []

    quotations = frappe.get_all("Supplier Quotation",
        filters={"supplier": supplier},
        fields=["name", "quotation_number", "transaction_date", "grand_total", "currency", "docstatus"],
        order_by="creation desc"
    )

    # Add docstatus label
    for q in quotations:
        q["docstatus_label"] = {
            0: "Draft",
            1: "Submitted",
            2: "Cancelled"
        }.get(q["docstatus"], "Draft")

    return quotations

@frappe.whitelist()
def save_supplier_quotation(name, quotation_number, items, attachments):
    doc = frappe.get_doc("Supplier Quotation", name)
    doc.quotation_number = quotation_number
    doc.terms = terms

    for item in items:
        for row in doc.items:
            if row.name == item["name"]:
                row.qty = item["qty"]
                row.rate = item["rate"]
                break

    doc.set("custom_attachments", [])  # clear and replace
    for attachment in attachments:
        doc.append("custom_attachments", {
            "file_url": attachment["file_url"],
            "description": attachment["description"]
        })

    doc.save()
    frappe.db.commit()
    return True

@frappe.whitelist()
def get_supplier_quotation(name):
    user = frappe.session.user
    supplier = frappe.db.get_value("Contact", {"email_id": user}, "supplier")
    if not supplier:
        frappe.throw(_("You are not linked to any Supplier."))

    quotation = frappe.get_doc("Supplier Quotation", quotation_name)
    if quotation.supplier != supplier:
        frappe.throw(_("You do not have access to this quotation."))

    attachments = frappe.get_all(
        "Custom Attachment",
        filters={"parenttype": "Supplier Quotation", "parent": quotation_name},
        fields=["name", "file_name", "file_url"]
    )

    return {
        "name": quotation.name,
        "supplier": quotation.supplier,
        "transaction_date": quotation.transaction_date,
        "items": quotation.items,
        "quotation_number": quotation.get("quotation_number"),
        "message_for_supplier": quotation.get("message_for_supplier"),
        "custom_attachments": attachments,
    }

@frappe.whitelist()
def update_supplier_quotation(doc):
    import json
    import frappe
    from frappe import _

    if isinstance(doc, str):
        doc = json.loads(doc)

    quotation = frappe.get_doc("Supplier Quotation", doc.get("name"))
    
    # Update quotation fields
    quotation.quotation_number = doc.get("quotation_number")
    quotation.terms = doc.get("terms")

    # Clear existing items and append new ones
    quotation.items = []

    for item in doc.get("items", []):
        item_code = item.get("item_code")

        # Ensure item_code exists in the Item DocType
        if not frappe.db.exists("Item", item_code):
            frappe.throw(_("Item {0} does not exist").format(item_code))

        # Append the item to the quotation items list
        quotation.append("items", {
            "item_code": item_code,  # This is the Linked Field for Item
            "qty": item.get("qty"),
            "rate": item.get("rate"),
            "uom": item.get("uom")
        })

    # Save the updated quotation
    quotation.save(ignore_permissions=True)
    return {"message": "Quotation updated successfully"}

@frappe.whitelist()
def delete_supplier_quotation(name):
    doc = frappe.get_doc("Supplier Quotation", name)
    if doc.owner != frappe.session.user:
        frappe.throw(_("Not authorized"))
    doc.delete()
    frappe.db.commit()

@frappe.whitelist()
def add_attachment(name, file_url, file_name):
    doc = frappe.get_doc("Supplier Quotation", name)
    doc.append("custom_attachments", {"file_url": file_url, "file_name": file_name})
    doc.save()
    frappe.db.commit()

@frappe.whitelist()
def remove_attachment(name, index):
    doc = frappe.get_doc("Supplier Quotation", name)
    if 0 <= index < len(doc.custom_attachments):
        doc.custom_attachments.pop(index)
    doc.save()

@frappe.whitelist()
def submit_supplier_quotation(quotation_name):
    # Get the quotation document
    quotation = frappe.get_doc("Supplier Quotation", quotation_name)

    # Ensure the user has permission to submit the document
    if not quotation.has_permission("submit"):
        frappe.throw(_("You do not have permission to submit this Supplier Quotation"))

    # Submit the quotation
    quotation.submit()
    return {"message": "Quotation submitted successfully"}

@frappe.whitelist()
def add_attachment_to_supplier_quotation(quotation, file_url, description=""):
    doc = frappe.get_doc("Supplier Quotation", quotation)

    doc.append("custom_attachments", {
        "file_url": file_url,
        "description": description
    })

    doc.save()
    frappe.db.commit()
    return True

@frappe.whitelist()
def patch_supplier_quotation(name, quotation_number=None, terms=None, updated_items=None):
    import json

    if isinstance(updated_items, str):
        updated_items = json.loads(updated_items)

    doc = frappe.get_doc("Supplier Quotation", name)

    if quotation_number is not None:
        doc.quotation_number = quotation_number
    if terms is not None:
        doc.terms = terms

    # Build a map for faster lookup
    updated_map = {item['item_code']: item for item in updated_items}

    for item in doc.items:
        if item.item_code in updated_map:
            update = updated_map[item.item_code]
            item.qty = update.get('qty', item.qty)
            item.rate = update.get('rate', item.rate)
            item.uom = update.get('uom', item.uom)
            # Keep all other fields untouched

    doc.save()
    return True

import frappe
