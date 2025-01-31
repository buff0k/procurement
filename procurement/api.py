import frappe
from frappe.utils.file_manager import get_file
from werkzeug.wrappers import Response

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
