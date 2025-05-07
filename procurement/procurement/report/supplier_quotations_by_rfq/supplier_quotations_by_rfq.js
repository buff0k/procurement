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
            "on_change": function () {
                let rfq = frappe.query_report.get_filter_value("request_for_quotation");
                if (rfq) {
                    frappe.call({
                        method: "procurement.procurement.report.supplier_quotations_by_rfq.supplier_quotations_by_rfq.get_rfq_metadata",
                        args: {
                            rfq: rfq
                        },
                        callback: function (r) {
                            if (r.message) {
                                const html = `
                                    <div class="rfq-info-box" style="margin: 15px 0; padding: 10px; background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 6px;">
                                        <strong>Required By:</strong> ${frappe.datetime.str_to_user(r.message.schedule_date)}<br>
                                        <strong>Local Community Procurement:</strong> ${r.message.custom_local_community_procurement || "N/A"}<br>
                                        <strong>Items:</strong> ${r.message.item_names.join(", ")}
                                    </div>
                                `;

                                // Cleanup previous info box
                                $(frappe.query_report.page.main).find('.rfq-info-box').remove();

                                // Inject safely into report page container
                                $(frappe.query_report.page.main).prepend(html);

                                // Refresh the report
                                frappe.query_report.refresh();
                            }
                        }
                    });
                }
            }
        }
    ],

    onload: function (report) {
        // Clean up any lingering boxes on reload
        $(report.page.main).find('.rfq-info-box').remove();

        report.page.add_inner_button(__('Refresh'), function () {
            report.refresh();
        });
    }
};
