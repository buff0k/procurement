# Copyright (c) 2025, Isambane Mining (Pty) Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"fieldname": "name", "label": _("PR Doc"), "fieldtype": "Link", "options": "Purchase Requisition", "width": 100},
        {"fieldname": "site_code", "label": _("Site"), "fieldtype": "Link", "options": "Site Code", "width": 50},
        {"fieldname": "date", "label": _("Date"), "fieldtype": "Date", "width": 120},
        {"fieldname": "pr_number", "label": _("PR No."), "fieldtype": "Int", "width": 100},
        {"fieldname": "account", "label": _("Cost Code"), "fieldtype": "Link", "options": "Account", "width": 100},
        {"fieldname": "asset", "label": _("Fleet No."), "fieldtype": "Link", "options": "Asset", "width": 100},
        {"fieldname": "req_name", "label": _("Requestor"), "fieldtype": "Data", "width": 150},
        {"fieldname": "division", "label": _("Div"), "fieldtype": "Select", "width": 20},
        {"fieldname": "component", "label": _("Component"), "fieldtype": "Data", "width": 150},
        {"fieldname": "description", "label": _("Description"), "fieldtype": "Data", "width": 200},
        {"fieldname": "supplier", "label": _("Supplier"), "fieldtype": "Link", "options": "Supplier", "width": 150},
        {"fieldname": "official_company_order_no", "label": _("Order No."), "fieldtype": "Data", "width": 150},
        {"fieldname": "subtotal", "label": _("Cost"), "fieldtype": "Currency", "width": 100},
        {"fieldname": "invoice_no", "label": _("Invoice No."), "fieldtype": "Data", "width": 150},
        {"fieldname": "invoice_count", "label": _("IC"), "fieldtype": "Int", "width": 20}
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql(f"""
        SELECT
            pr.name,
            pr.site_code,
            pr.date,
            pr.pr_number,
            pr.division,
            pr.account,
            pr.asset,
            pr.req_name,
            pr.component,
            GROUP_CONCAT(il.description_and_part_no SEPARATOR ', ') AS description,
            pr.supplier,
            pr.official_company_order_no,
            pr.subtotal,
            GROUP_CONCAT(ad.doc_no SEPARATOR ', ') AS invoice_no,
            pr.invoice_count
        FROM
            `tabPurchase Requisition` pr
        LEFT JOIN
            `tabPurchase Requisition List` il ON pr.name = il.parent
        LEFT JOIN
            `tabAttach Documents` ad ON pr.name = ad.parent AND ad.document_type = 'Tax Invoice'
        WHERE
            1=1
            {conditions}
        GROUP BY
            pr.name
        ORDER BY
            pr.date DESC
    """, as_dict=True)

    return data

def get_conditions(filters):
    conditions = ""
    if filters.get("start_date"):
        conditions += f" AND pr.date >= '{filters.get('start_date')}'"
    if filters.get("end_date"):
        conditions += f" AND pr.date <= '{filters.get('end_date')}'"
    if filters.get("site_code"):
        conditions += f" AND pr.site_code = '{filters.get('site_code')}'"
    return conditions
