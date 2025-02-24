// Copyright (c) 2025, Isambane Mining (Pty) Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["Procurement Order Status"] = {
	"filters": [
        {
            "fieldname": "start_date",
            "label": "Start Date",
            "fieldtype": "Date",
            "default": ""
        },
        {
            "fieldname": "end_date",
            "label": "End Date",
            "fieldtype": "Date",
            "default": ""
        },
        {
            "fieldname": "site_code",
            "label": "Site",
            "fieldtype": "Link",
            "options": "Site Code",
            "default": ""
        }
    ],

    formatter: function (value, row, column, data, default_formatter) {
        // Apply default formatting first
        value = default_formatter(value, row, column, data);

        // Determine text color
        let text_color = "";
        if (!data["official_company_order_no"]) {
            text_color = "#D4A017"; // Golden Yellow (Better Visibility)
        } else if (!data["invoice_no"]) {
            text_color = "#FF0000"; // Red
        }

        // Apply text color
        if (text_color) {
            return `<span style="color: ${text_color};">${value}</span>`;
        }

        return value;
    },
};
