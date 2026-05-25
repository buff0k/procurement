frappe.ui.form.on("Parts Requisition Item", {
	item_group(frm, cdt, cdn) {
		const row = locals[cdt][cdn];

		if (row.item_group) {
			row.item_code = "";
			frm.refresh_field("items_section");
		}
	},

	item_code(frm, cdt, cdn) {
		const row = locals[cdt][cdn];

		if (!row.item_group) {
			row.item_code = "";
			frm.refresh_field("items_section");
			frappe.msgprint(__("Select Item Group before Item Code."));
		}
	}
});


frappe.ui.form.on("Parts Requisition", {
	refresh(frm) {
		set_account_filter(frm);

		if (frm.doc.plant_no) {
			load_asset_details(frm);
		}
	},

	onload(frm) {
		set_account_filter(frm);
	},

	company(frm) {
		frm.set_value("plant_no", "");
		frm.set_value("asset_category", "");
		frm.set_value("model", "");
		frm.set_value("vin_no", "");

		(frm.doc.items_section || []).forEach(row => {
			row.item_group = "";
			row.item_code = "";
		});

		frm.refresh_field("items_section");

		set_account_filter(frm);
	},

	site(frm) {
		frm.set_value("plant_no", "");
		frm.set_value("asset_category", "");
		frm.set_value("model", "");
		frm.set_value("vin_no", "");

		(frm.doc.items_section || []).forEach(row => {
			row.item_group = "";
			row.item_code = "";
		});

		frm.refresh_field("items_section");

		set_account_filter(frm);
	},

	plant_no(frm) {
		if (!frm.doc.plant_no) {
			return;
		}

		if (!frm.doc.company || !frm.doc.site) {
			frm.set_value("plant_no", "");
			frappe.msgprint(__("Select Company and Site before Plant No."));
			return;
		}

		load_asset_details(frm);
	},

	asset_category(frm) {
		(frm.doc.items_section || []).forEach(row => {
			row.item_group = "";
			row.item_code = "";
		});

		frm.refresh_field("items_section");
	}
});


function set_account_filter(frm) {
	frm.set_query("plant_no", function() {
		if (!frm.doc.company || !frm.doc.site) {
			return {
				filters: {
					name: ["=", ""]
				}
			};
		}

		return {
			query: "procurement.procurement.doctype.parts_requisition.parts_requisition.get_assets_by_site_code",
			filters: {
				company: frm.doc.company,
				site: frm.doc.site
			}
		};
	});

	frm.set_query("item_group", "items_section", function(doc, cdt, cdn) {
		if (!frm.doc.asset_category) {
			return {
				filters: {
					name: ["=", ""]
				}
			};
		}

		return {
			query: "procurement.procurement.doctype.parts_requisition.parts_requisition.get_item_groups_by_asset_category",
			filters: {
				asset_category: frm.doc.asset_category
			}
		};
	});

	frm.set_query("item_code", "items_section", function(doc, cdt, cdn) {
		const row = locals[cdt][cdn];

		if (!frm.doc.asset_category || !row.item_group) {
			return {
				filters: {
					name: ["=", ""]
				}
			};
		}

		return {
			filters: {
				item_group: row.item_group,
				disabled: 0
			}
		};
	});
}


function split_item_code(item_code) {
	if (!item_code) {
		return {
			plant_make: "",
			model: ""
		};
	}

	const cleaned = String(item_code).trim().replace(/\s+/g, " ");
	const parts = cleaned.split(" ");

	if (parts.length === 1) {
		return {
			plant_make: parts[0],
			model: parts[0]
		};
	}

	const plant_make = parts[parts.length - 1];
	const model = parts.slice(0, -1).join(" ");

	return {
		plant_make: plant_make || "",
		model: model || ""
	};
}


function load_asset_details(frm) {
	if (!frm.doc.plant_no) {
		frm.set_value("asset_category", "");
		frm.set_value("model", "");
		frm.set_value("vin_no", "");
		return;
	}

	frappe.db.get_doc("Asset", frm.doc.plant_no)
		.then(doc => {
			const item_code = doc.item_code || "";
			const split_values = split_item_code(item_code);

			const current_vin = frm.doc.vin_no || "";

			const vin_no =
				current_vin ||
				doc.vin_no ||
				doc.serial_no ||
				doc.chassis_no ||
				doc.custom_vin_no ||
				"";

			frm.set_value("asset_category", doc.asset_category || "");
			frm.set_value("model", split_values.model);

			if (!frm.doc.vin_no) {
				frm.set_value("vin_no", vin_no);
			}
		})
		.catch(err => {
			console.error("Failed to load Asset details", err);

			frm.set_value("asset_category", "");
			frm.set_value("model", "");
			frm.set_value("vin_no", "");

			frappe.msgprint(__("Could not load Plant Make / Model from Asset."));
		});
}