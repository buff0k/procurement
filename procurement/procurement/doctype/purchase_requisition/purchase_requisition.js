// Copyright (c) 2024, Isambane Mining (Pty) Ltd and contributors
// For license information, please see license.txt

frappe.ui.form.on('Purchase Requisition', {
    company: function(frm) {
        if (frm.doc.company) {
            frappe.db.get_value('Company', frm.doc.company, ['default_letter_head', 'abbr'], (r) => {
                frm.set_value('letterhead', r.default_letter_head);
                frm.set_value('company_abbr', r.abbr);
            });
        }
    },

    refresh: function(frm) {
        frm.fields_dict['item_list'].grid.wrapper.on('change', 'input[data-fieldname="qty"], input[data-fieldname="unit_price"]', function() {
            calculate_total_cost(frm);
            calculate_totals(frm);
        });
    },

    validate: function(frm) {
        calculate_totals(frm);
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
