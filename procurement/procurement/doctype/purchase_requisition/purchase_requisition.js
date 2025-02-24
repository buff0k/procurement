// Copyright (c) 2024, Isambane Mining (Pty) Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Requisition', {
    company: function (frm) {
        if (frm.doc.company) {
            // Call server script to fetch company details
            frappe.call({
                method: "procurement.procurement.doctype.purchase_requisition.purchase_requisition.get_company_details",
                args: { company: frm.doc.company },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value("letter_head", r.message.default_letter_head);
                        frm.set_value("company_abbr", r.message.company_abbr);
                    }
                }
            });
        } else {
            // Clear fields if company is unset
            frm.set_value("letter_head", null);
            frm.set_value("company_abbr", null);
        }
    },

    refresh: function(frm) {
        frm.fields_dict['item_list'].grid.wrapper.on('change', 'input[data-fieldname="qty"], input[data-fieldname="unit_price"]', function() {
            calculate_total_cost(frm);
            calculate_totals(frm);
        });
        frm.trigger('update_employee_names');
        // Check if the user has the "Procurement Admin" role
        if (frappe.user.has_role('Procurement Admin')) {
            // Add a custom button to the form
            frm.add_custom_button(__('Generate Order Number'), function() {
                // Call the server-side method using the full module path
                frappe.call({
                    method: "procurement.procurement.doctype.purchase_requisition.purchase_requisition.generate_order_number",
                    args: {
                        doc: frm.doc.name
                    },
                    callback: function(r) {
                        if (r.exc) {
                            frappe.msgprint(__("Error: {0}").format(r.exc));
                        } else {
                            frm.refresh();
                        }
                    }
                });
            });
        }
    },

    validate: function(frm) {
        calculate_totals(frm);
    },

    // Trigger the update when the linked fields are changed
    requested_by: function (frm) {
        frm.trigger('update_employee_names');
    },
    deliver_to: function (frm) {
        frm.trigger('update_employee_names');
    },
    authorized_by: function (frm) {
        frm.trigger('update_employee_names');
    },

    update_employee_names: function (frm) {
        if (frm.doc.requested_by) {
            frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Employee",
                    filters: { name: frm.doc.requested_by },
                    fieldname: "employee_name"
                },
                callback: function (r) {
                    frm.set_value("req_name", r.message.employee_name);
                }
            });
        }

        if (frm.doc.deliver_to) {
            frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Employee",
                    filters: { name: frm.doc.deliver_to },
                    fieldname: "employee_name"
                },
                callback: function (r) {
                    frm.set_value("del_name", r.message.employee_name);
                }
            });
        }

        if (frm.doc.authorized_by) {
            frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Employee",
                    filters: { name: frm.doc.authorized_by },
                    fieldname: "employee_name"
                },
                callback: function (r) {
                    frm.set_value("auth_name", r.message.employee_name);
                }
            });
        }
    },

    site_code: function (frm) {
        if (frm.doc.site_code) {
            // Fetch the location from the linked Site Code document
            frappe.db.get_value('Site Code', frm.doc.site_code, 'location', (r) => {
                if (r && r.location) {
                    // Set the location field in the Purchase Requisition document
                    frm.set_value('location', r.location);
                }
            });
        
            // Fetch Buyer using custom server-side method
            frappe.call({
                method: "procurement.procurement.doctype.purchase_requisition.purchase_requisition.get_buyer_for_site",
                args: { site_code: frm.doc.site_code },
                callback: function(response) {
                    if (response.message) {
                        frm.set_value("buyer", response.message);
                    } else {
                        frm.set_value("buyer", null);
                    }
                }
            });
        
        } else {
            // Clear fields if site_code is not set
            frm.set_value('location', null);
            frm.set_value('buyer', null);
        }
    }
});

frappe.ui.form.on('Purchase Requisition List', {
    qty: function(frm, cdt, cdn) {
        update_row_totals(frm, cdt, cdn);
    },

    unit_price: function(frm, cdt, cdn) {
        update_row_totals(frm, cdt, cdn);
    },

    item: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.item) {
            frappe.db.get_value('Item', row.item, 'item_name', (r) => {
                frappe.model.set_value(cdt, cdn, 'description_and_part_no', r.item_name);
            });
        }
    }
});

function update_row_totals(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    row.total_cost = row.qty * row.unit_price;
    frm.refresh_field('item_list');
    calculate_totals(frm);
}

function calculate_total_cost(frm) {
    frm.doc.item_list.forEach(row => {
        row.total_cost = row.qty * row.unit_price;
    });
    frm.refresh_field('item_list');
}

function calculate_totals(frm) {
    let subtotal = 0;
    frm.doc.item_list.forEach(row => {
        subtotal += row.total_cost;
    });
    frm.set_value('subtotal', subtotal);

    let vat = subtotal * 0.15;
    frm.set_value('vat', vat);

    frm.set_value('total', subtotal + vat);
}
