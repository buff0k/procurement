import frappe

@frappe.whitelist()
def get_rfq_image(file_url):
    """Returns a publicly accessible URL for a private RFQ image"""
    # Ensure only valid private file paths are processed
    if not file_url.startswith("/private/files/"):
        frappe.throw("Invalid file path")

    # Fetch the file document
    file_doc = frappe.get_doc("File", {"file_url": file_url})

    # Ensure the file is linked to a Request for Quotation
    if file_doc.attached_to_doctype != "Request for Quotation":
        frappe.throw("Unauthorized access")

    # Construct full URL for the file
    site_url = frappe.utils.get_url()
    full_url = f"{site_url}{file_url}"

    return {"url": full_url}
