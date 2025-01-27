// Copyright (c) 2024, Isambane Mining (Pty) Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Requisition', {
   if (frm.doc.company) {
            // Fetch default_letter_head from the Company DocType
            frappe.db.get_value('Company', frm.doc.company, 'default_letter_head', (r) => {
                frm.set_value('letter_head', r.default_letter_head);
            });

            // Fetch company_abbr from the Company Abbreviations DocType
            frappe.db.get_value('Company Abbreviations', { company: frm.doc.company }, 'company_abbr', (r) => {
                if (r) {
                    frm.set_value('company_abbr', r.company_abbr);
                } else {
                    frm.set_value('company_abbr', null); // Clear the field if no match is found
                }
            });

            // Apply filter on the "code" field linked to the "Account" DocType
            frm.set_query('code', function () {
                return {
                    filters: {
                        company: frm.doc.company
                    }
                };
            });

            // Apply filter on the "location" field linked to the "Cost Center" DocType
            frm.set_query('location', function () {
                return {
                    filters: {
                        company: frm.doc.company
                    }
                };
            });
        } else {
            // Clear letter_head and company_abbr if company field is empty
            frm.set_value('letter_head', null);
            frm.set_value('company_abbr', null);
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
