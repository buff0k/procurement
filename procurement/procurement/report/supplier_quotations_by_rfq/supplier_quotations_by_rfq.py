# Copyright (c) 2025, Isambane Mining (Pty) Ltd and contributors
# For license information, please see license.txt

import frappe
from collections import defaultdict

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

    # First column: Supplier Quotation Link
    columns = [
        {"fieldname": "supplier_quotation", "label": "Supplier Quotation", "fieldtype": "Link", "options": "Supplier Quotation", "width": 150},
        {"fieldname": "supplier_name", "label": "Supplier", "fieldtype": "Link", "options": "Supplier", "width": 150}
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

        # If supplier not already in the map, initialize their data
        if supplier_name not in supplier_map:
            supplier_map[supplier_name] = {"supplier_quotation": supplier_quotation, "supplier_name": supplier_name}

        # Add item-specific details
        supplier_map[supplier_name][f"{item['item_code']}_uom"] = item["uom"]
        supplier_map[supplier_name][f"{item['item_code']}_qty"] = item["qty"]
        supplier_map[supplier_name][f"{item['item_code']}_price"] = item["rate"]
        supplier_map[supplier_name][f"{item['item_code']}_total"] = item["amount"]

    # Convert dictionary to list format for the report
    data = list(supplier_map.values())

    return data