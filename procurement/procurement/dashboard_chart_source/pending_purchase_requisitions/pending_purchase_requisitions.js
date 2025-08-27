// Copyright (c) 2025, Isambane Mining (Pty) Ltd and contributors
// For license information, please see license.txt

frappe.dashboards.chart_sources["Pending Purchase Requisitions"] = {
  method:
    "procurement.procurement.dashboard_chart_source.pending_purchase_requisitions.pending_purchase_requisitions.get_data",
  // Optional: expose filters in the chart dialog
  // filters: [
  //   { fieldname: "company", label: __("Company"), fieldtype: "Link", options: "Company" }
  // ]
};
