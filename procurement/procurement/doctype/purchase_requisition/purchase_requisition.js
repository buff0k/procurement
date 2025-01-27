// Copyright (c) 2024, Isambane Mining (Pty) Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Requisition', {
   onload: function (frm) {
        // Set the default company on load
        if (!frm.doc.company) {
            frappe.call({
                method: "frappe.client.get_value",
                args: {
                    doctype: "Global Defaults",
                    fieldname: "default_company",
                },
                callback: function (r) {
                    if (r.message && r.message.default_company) {
                        frm.set_value("company", r.message.default_company);
                    }
                }
            });
        }
    },

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
        if (frappe.user.has_role('Procurement Admin')) {
            frm.set_df_property('official_company_order_no', 'read_only', 0);
            frm.set_df_property('code', 'read_only', 0);
            frm.set_df_property('location', 'read_only', 0);
            frm.add_custom_button(__('Create Purchase Order'), function() {
                frappe.model.open_mapped_doc({
                    method: 'procurement.procurement.doctype.purchase_requisition.purchase_requisition.make_purchase_order',
                    frm: frm
                });
            });
        } else {
            // Set fields to read-only for all other roles
            frm.set_df_property('official_company_order_no', 'read_only', 1);
            frm.set_df_property('code', 'read_only', 1);
            frm.set_df_property('location', 'read_only', 1);
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
        } else {
            // Clear the location field if site_code is not set
            frm.set_value('location', null);
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
