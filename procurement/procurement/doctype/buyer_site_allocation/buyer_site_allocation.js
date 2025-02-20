// Copyright (c) 2025, Isambane Mining (Pty) Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on("Buyer Site Allocation", {
    refresh: function(frm) {

    },
});

frappe.ui.form.on('Site Code List', {
    site_code: function(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
        if (row.site_code) {
            frappe.db.get_value('Site Code', row.site_code, 'location', function(data) {
                if (data && data.location) {
                    frappe.model.set_value(cdt, cdn, 'location', data.location);
                }
            });
        }
    }
});