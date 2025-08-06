// Copyright (c) 2025, Isambane Mining (Pty) Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Local Suppliers', {
    refresh: function(frm) {
    }
});

// Listen for changes in the supplier_name field in the esd_suppliers child table
frappe.ui.form.on("ESD Supplier List", "supplier_name", function(frm, cdt, cdn) {

    // Get the current row data from the child table
    var item = locals[cdt][cdn]; // Access the current row

    // Check if supplier_name is not empty
    if (item.supplier_name) {
        // Fetch contact email_id and mobile_no from Supplier doctype
        frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Supplier',
                name: item.supplier_name
            },
            callback: function(response) {
                if (response.message) {
                    let supplier = response.message;

                    // Update contact, email_id and mobile_no in the current child table row
                    frappe.model.set_value(cdt, cdn, 'contact', supplier.supplier_primary_contact || '');
                    frappe.model.set_value(cdt, cdn, 'email_id', supplier.email_id || '');
                    frappe.model.set_value(cdt, cdn, 'mobile_no', supplier.mobile_no || '');

                    // Refresh the child table to show the updated values
                    frm.refresh_field('esd_suppliers');
                } 
            }
        });
    }
});
