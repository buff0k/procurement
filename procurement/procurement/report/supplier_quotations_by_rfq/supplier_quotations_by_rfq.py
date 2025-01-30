# Copyright (c) 2025, Isambane Mining (Pty) Ltd and contributors
# For license information, please see license.txt

import frappe
import re
from collections import defaultdict

def strip_html_tags(html):
    """Remove HTML tags and return plain text."""
    if not html:
        return ""
    return re.sub("<.*?>", "", html)  # Strip all HTML tags

def execute(filters=None):
    if not filters:
        filters = {}

    if not filters.get("request_for_quotation"):
        frappe.throw("Please select a Request for Quotation to run the report.")

    columns = get_columns(filters)
    data = get_data(filters)

    return columns, data

def get_columns(filters):
    """Define table columns dynamically based on RFQ items."""

    # Supplier-related columns
    columns = [
        {"fieldname": "supplier_quotation", "label": "Supplier Quotation", "fieldtype": "Link", "options": "Supplier Quotation", "width": 150},
        {"fieldname": "supplier_name", "label": "Supplier", "fieldtype": "Link", "options": "Supplier", "width": 150},
        {"fieldname": "supplier_primary_address", "label": "Supplier Address", "fieldtype": "Data", "width": 200},
        {"fieldname": "mobile_no", "label": "Supplier Contact No.", "fieldtype": "Data", "width": 150},
        {"fieldname": "email_id", "label": "Supplier Email Address", "fieldtype": "Data", "width": 200},
    ]

    # Fetch unique items for the given RFQ
    item_codes = frappe.get_all(
        "Supplier Quotation Item",
        filters={"request_for_quotation": filters.get("request_for_quotation")},
        distinct=True,
        pluck="item_code"
    )

    # Dynamically create columns for each item
    for item in item_codes:
        columns.extend([
            {"fieldname": f"{item}_uom", "label": f"{item} UOM", "fieldtype": "Data", "width": 100},
            {"fieldname": f"{item}_qty", "label": f"{item} Quantity", "fieldtype": "Float", "width": 100},
            {"fieldname": f"{item}_price", "label": f"{item} Price per Unit", "fieldtype": "Currency", "width": 120},
            {"fieldname": f"{item}_total", "label": f"{item} Total Price", "fieldtype": "Currency", "width": 120},
        ])

    # Add the Total and Notes columns at the end
    columns.extend([
        {"fieldname": "total_amount", "label": "Total", "fieldtype": "Currency", "width": 150},
        {"fieldname": "terms", "label": "Notes", "fieldtype": "Data", "width": 300}
    ])

    return columns

def get_data(filters):
    """Fetch supplier quotations for the given RFQ and restructure them into columns."""

    # Step 1: Get all Supplier Quotations linked via items
    supplier_quotation_ids = frappe.get_all(
        "Supplier Quotation Item",
        filters={"request_for_quotation": filters.get("request_for_quotation")},
        distinct=True,
        pluck="parent"
    )

    # Step 2: Fetch Supplier Quotation data
    supplier_quotations = frappe.get_all(
        "Supplier Quotation",
        filters={"name": ["in", supplier_quotation_ids]},
        fields=["name", "supplier", "terms"]
    )

    # Step 3: Fetch all Supplier Quotation Items
    sq_items = frappe.get_all(
        "Supplier Quotation Item",
        filters={"parent": ["in", supplier_quotation_ids]},
        fields=["parent", "item_code", "qty", "rate", "amount", "uom"]
    )

    # Dictionary to store supplier data
    supplier_map = {}

    # Step 4: Initialize all suppliers first
    for sq in supplier_quotations:
        supplier_details = frappe.get_value(
            "Supplier",
            sq.supplier,
            ["supplier_primary_address", "mobile_no", "email_id"],
            as_dict=True
        )

        supplier_map[sq.name] = {
            "supplier_quotation": sq.name,
            "supplier_name": sq.supplier,
            "supplier_primary_address": supplier_details.get("supplier_primary_address"),
            "mobile_no": supplier_details.get("mobile_no"),
            "email_id": supplier_details.get("email_id"),
            "total_amount": 0,
            "terms": strip_html_tags(sq.terms) if sq.terms else ""
        }

    # Step 5: Populate item data
    for item in sq_items:
        if item["parent"] in supplier_map:
            supplier_map[item["parent"]][f"{item['item_code']}_uom"] = item["uom"]
            supplier_map[item["parent"]][f"{item['item_code']}_qty"] = item["qty"]
            supplier_map[item["parent"]][f"{item['item_code']}_price"] = item["rate"]
            supplier_map[item["parent"]][f"{item['item_code']}_total"] = item["amount"]
            supplier_map[item["parent"]]["total_amount"] += item["amount"]

    # Step 6: Convert dictionary to list format for the report
    data = list(supplier_map.values())

    return data
