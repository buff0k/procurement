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

    onload: function(report) {
        // This function can be used to handle other onload actions for the report
    },
    // If you need any custom logic on filter changes, you can use this method
    filter: function() {
        // Custom logic for when the filter changes can go here
    }
};
