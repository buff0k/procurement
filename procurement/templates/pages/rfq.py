# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
# Changes made to original by BuFf0k

import frappe
import re
from frappe import _
from frappe.utils import formatdate
from erpnext.controllers.website_list_for_contact import get_customers_suppliers

def get_context(context):
	context.no_cache = 1
	context.show_sidebar = True

	# BuFf0k - Fix Context Issues
	if not frappe.form_dict.get("name"):
		frappe.throw(_("RFQ Name not provided"))

	# BuFf0k - Fix Context Issues by manually fetching RFQ Document
	try:
		context.doc = frappe.get_doc("Request for Quotation", frappe.form_dict.name)
	except frappe.DoesNotExistError:
		frappe.throw(_("RFQ not found"))

	# Original Frappe Code
	context.parents = frappe.form_dict.parents
	context.doc.supplier = get_supplier()
	context.doc.rfq_links = get_link_quotation(context.doc.supplier, context.doc.name)
	unauthorized_user(context.doc.supplier)
	update_supplier_details(context)
	context["title"] = frappe.form_dict.name

	# BuFf0k = Fetch custom_details_about_rfq_boq_etc field and include it in the context
	context.custom_details_about_rfq_boq_etc = process_rfq_images(context.doc.custom_details_about_rfq_boq_etc)

# BuFf0k fucntion to use api call to handle images for RFQs
def process_rfq_images(html_content):
	"""Find all private file URLs and replace them with API-accessible URLs, stripping ?fid=..."""
	if not html_content:
		return ""

	# Regex to find private file URLs and strip ?fid=...
	private_file_pattern = r'(["\'])/private/files/([^"\']+)(\?fid=[^"\']*)?(["\'])'

	def replace_url(match):
		original_url = match.group(2)  # Extract only the file path (strip ?fid=...)
		return f'{match.group(1)}/api/method/procurement.api.get_rfq_image?file_url=/private/files/{original_url}{match.group(4)}'

	return re.sub(private_file_pattern, replace_url, html_content)

# BuFf0k - Modified get_supplier function to avoid Context Issues
def get_supplier():
	parties_doctype = "Request for Quotation Supplier"
	# Log what we're sending
	frappe.log_error(f"Fetching suppliers for: {parties_doctype}", "RFQ Debug")
	customers, suppliers = get_customers_suppliers(parties_doctype, frappe.session.user)
	return suppliers[0] if suppliers else ""

def check_supplier_has_docname_access(supplier):
	status = True
	if frappe.form_dict.name not in frappe.db.sql_list(
		"""select parent from `tabRequest for Quotation Supplier`
		where supplier = %s""",
		(supplier,),
	):
		status = False
	return status


def unauthorized_user(supplier):
	status = check_supplier_has_docname_access(supplier) or False
	if status is False:
		frappe.throw(_("Not Permitted"), frappe.PermissionError)


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


def get_link_quotation(supplier, rfq):
	quotation = frappe.db.sql(
		""" select distinct `tabSupplier Quotation Item`.parent as name,
		`tabSupplier Quotation`.status, `tabSupplier Quotation`.transaction_date from
		`tabSupplier Quotation Item`, `tabSupplier Quotation` where `tabSupplier Quotation`.docstatus < 2 and
		`tabSupplier Quotation Item`.request_for_quotation =%(name)s and
		`tabSupplier Quotation Item`.parent = `tabSupplier Quotation`.name and
		`tabSupplier Quotation`.supplier = %(supplier)s order by `tabSupplier Quotation`.creation desc""",
		{"name": rfq, "supplier": supplier},
		as_dict=1,
	)

	for data in quotation:
		data.transaction_date = formatdate(data.transaction_date)

	return quotation or None
