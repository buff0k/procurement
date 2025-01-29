// Copyright (c) 2025, Isambane Mining (Pty) Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["Supplier Quotations by RFQ"] = {
    "filters": [
        {
            "fieldname": "request_for_quotation",
            "label": "Request for Quotation",
            "fieldtype": "Link",
            "options": "Request for Quotation",
            "reqd": 1,
        }
    ],
    onload: function(report) {
        report.page.add_inner_button(__('Refresh'), function() {
            report.refresh();
        });
    },
    filter: function() {
        // Custom logic for when the filter changes can go here
    }
};