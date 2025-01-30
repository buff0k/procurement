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

    # Fetch all supplier quotation items for the RFQ
    sq_items = frappe.get_all(
        "Supplier Quotation Item",
        filters={"request_for_quotation": filters.get("request_for_quotation")},
        fields=["parent", "item_code", "qty", "rate", "amount", "uom"]
    )

    # Dictionary to store supplier data
    supplier_map = {}

    for item in sq_items:
        supplier_quotation = item["parent"]
        supplier_name = frappe.get_value("Supplier Quotation", supplier_quotation, "supplier")

        # Fetch supplier details + Terms field from Supplier Quotation
        supplier_details = frappe.get_value(
            "Supplier",
            supplier_name,
            ["supplier_primary_address", "mobile_no", "email_id"],
            as_dict=True
        )

        # Fetch and clean the Terms field (convert HTML to plain text)
        raw_terms = frappe.get_value("Supplier Quotation", supplier_quotation, "terms")
        terms = strip_html_tags(raw_terms)  # Convert to plain text

        # If supplier not already in the map, initialize their data
        if supplier_name not in supplier_map:
            supplier_map[supplier_name] = {
                "supplier_quotation": supplier_quotation,
                "supplier_name": supplier_name,
                "supplier_primary_address": supplier_details.get("supplier_primary_address"),
                "mobile_no": supplier_details.get("mobile_no"),
                "email_id": supplier_details.get("email_id"),
                "total_amount": 0,  # Initialize total amount
                "terms": terms  # Store cleaned terms
            }

        # Add item-specific details
        supplier_map[supplier_name][f"{item['item_code']}_uom"] = item["uom"]
        supplier_map[supplier_name][f"{item['item_code']}_qty"] = item["qty"]
        supplier_map[supplier_name][f"{item['item_code']}_price"] = item["rate"]
        supplier_map[supplier_name][f"{item['item_code']}_total"] = item["amount"]

        # Sum total price for all items
        supplier_map[supplier_name]["total_amount"] += item["amount"]

    # Convert dictionary to list format for the report
    data = list(supplier_map.values())

    return data
