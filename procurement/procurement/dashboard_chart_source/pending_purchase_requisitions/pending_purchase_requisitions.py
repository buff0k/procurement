# Copyright (c) 2025, Isambane Mining (Pty) Ltd and contributors
# For license information, please see license.txt

import math
import frappe

LOCATION_FIELD = "location"  # change if it's location_cf, etc.

@frappe.whitelist()
def get_data(filters=None):
    filters = filters or {}
    where, params = ["docstatus = 0"], {}

    if filters.get("company"):
        where.append("company = %(company)s")
        params["company"] = filters["company"]

    rows = frappe.db.sql(f"""
        SELECT COALESCE(`{LOCATION_FIELD}`, 'Not Set') AS loc, COUNT(*) AS cnt
        FROM `tabPurchase Requisition`
        WHERE {" AND ".join(where)}
        GROUP BY COALESCE(`{LOCATION_FIELD}`, 'Not Set')
        ORDER BY cnt DESC
    """, params, as_dict=True)

    # x-axis labels are the locations themselves
    labels = [r["loc"] for r in rows]

    # one dataset per location; only fill the value at that location's index, None elsewhere
    datasets = []
    for i, r in enumerate(rows):
        values = [None] * len(labels)
        values[i] = int(r["cnt"])
        datasets.append({
            "name": r["loc"],            # shows in legend
            "values": values,            # only one real value → one bar per label
            "color": _color_from_label(r["loc"]),
        })

    return {
        "labels": labels,
        "datasets": datasets,
        "type": "bar",
        "barOptions": {"stacked": 0, "spaceRatio": 0.2},
        "valuesOverPoints": 1
    }

def _color_from_label(label: str) -> str:
    # deterministic HSL->HEX based on label text
    s = (label or "Not Set")
    h = 0
    for ch in s:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    hue = h % 360
    return _hsl_to_hex(hue, 65, 55)

def _hsl_to_hex(h: int, s: int, l: int) -> str:
    s /= 100.0; l /= 100.0
    c = (1 - abs(2*l - 1)) * s
    x = c * (1 - abs((h / 60.0) % 2 - 1))
    m = l - c/2
    r = g = b = 0
    if 0 <= h < 60:   r, g, b = c, x, 0
    elif h < 120:     r, g, b = x, c, 0
    elif h < 180:     r, g, b = 0, c, x
    elif h < 240:     r, g, b = 0, x, c
    elif h < 300:     r, g, b = x, 0, c
    else:             r, g, b = c, 0, x
    r = math.floor((r + m) * 255)
    g = math.floor((g + m) * 255)
    b = math.floor((b + m) * 255)
    return "#{:02X}{:02X}{:02X}".format(r, g, b)
