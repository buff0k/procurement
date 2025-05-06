// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

rfq = class rfq {
	constructor(){
		this.onfocus_select_all();
		this.change_qty();
		this.change_rate();
		this.terms();
		this.submit_rfq();
		this.navigate_quotations();
	}

	onfocus_select_all(){
		$("input").click(function(){
			$(this).select();
		})
	}

	change_qty(){
		$('.rfq-qty').change((e) => {
			const idx = $(e.currentTarget).data('idx');
			const qty = parseFloat($(e.currentTarget).val()) || 0;
			const rateInput = $(`.rfq-rate[data-idx="${idx}"]`);
			const rate = parseFloat(rateInput.val()) || 0;
			this.update_qty_rate(idx, qty, rate);
		});
	}
	
	change_rate(){
		$('.rfq-rate').change((e) => {
			const idx = $(e.currentTarget).data('idx');
			const rate = parseFloat($(e.currentTarget).val()) || 0;
			const qtyInput = $(`.rfq-qty[data-idx="${idx}"]`);
			const qty = parseFloat(qtyInput.val()) || 0;
			this.update_qty_rate(idx, qty, rate);
		});
	}

	terms(){
		$(".terms").on("change", ".terms-feedback", function(){
			doc.terms = $(this).val();
		})
	}

	update_qty_rate(idx, qty, rate) {
		doc.grand_total = 0.0;
	
		doc.items.forEach((item) => {
			if (item.idx === idx) {
				item.qty = qty;
				item.rate = rate;
				item.amount = rate * qty;
				$(`.rfq-amount[data-idx="${idx}"]`).text(format_number(item.amount, doc.number_format, 2));
			}
			doc.grand_total += item.amount || 0.0;
		});
	
		$('.tax-grand-total').text(format_number(doc.grand_total, doc.number_format, 2));
	}

	submit_rfq(){
		$(document).on("click", ".btn-sm", function(){
			// Update doc.items with the latest values from the form
			if (doc && doc.items) {
				doc.items.forEach(item => {
					const idx = item.idx;
	
					// Get updated qty, rate, and uom from the DOM
					const qty = $(`.rfq-qty[data-idx="${idx}"]`).val();
					const rate = $(`.rfq-rate[data-idx="${idx}"]`).val();
					const uom = $(`.rfq-uom[data-idx="${idx}"]`).val();
	
					// Update item
					item.qty = parseFloat(qty || item.qty);
					item.rate = parseFloat(rate || 0);
					item.uom = uom || item.uom;
				});
			}
	
			frappe.freeze();
			frappe.call({
				type: "POST",
				method: "erpnext.buying.doctype.request_for_quotation.request_for_quotation.create_supplier_quotation",
				args: {
					doc: doc
				},
				callback: function(r){
					frappe.unfreeze();
					if(r.message){
						$('.btn-sm').hide();
						window.location.href = "/supplier_quotation_list/" + encodeURIComponent(r.message);
					}
				}
			});
		});
	}

	navigate_quotations() {
		$('.quotations').click(function(){
			name = $(this).attr('idx')
			window.location.href = "/quotations/" + encodeURIComponent(name);
		})
	}
}