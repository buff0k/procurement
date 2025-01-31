import frappe
from frappe.utils.file_manager import get_file

@frappe.whitelist(allow_guest=True)
def get_rfq_image(file_url):
    """Serves private RFQ images directly"""

    # Ensure only valid private file paths are processed
    if not file_url.startswith("/private/files/"):
        frappe.throw("Invalid file path")

    # Fetch only the file attached to an RFQ
    file_doc = frappe.db.get_value(
        "File", 
        {"file_url": file_url, "attached_to_doctype": "Request for Quotation"}, 
        ["name", "attached_to_doctype", "attached_to_name"], 
        as_dict=True
    )

    # If no matching file is found, deny access
    if not file_doc:
        frappe.throw("Unauthorized access")

    # Read and return the actual file content
    return get_file(file_url)
