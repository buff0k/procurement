frappe.ready(() => {
    const quotationName = document.getElementById("quotation-container").dataset.doc;

    // Save Quotation
    document.getElementById("save-quotation").addEventListener("click", async () => {
        try {
            // Step 1: Fetch full doc from the backend
            const r = await frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Supplier Quotation",
                    name: quotationName
                }
            });

            const doc = r.message;
            doc.quotation_number = document.getElementById("quotation_number").value || "";
            doc.terms = document.getElementById("terms").value || "";

            // Step 2: Build a map of updated values from the UI
            const updates = {};
            document.querySelectorAll("#items-table tbody tr").forEach(row => {
                const itemCode = row.querySelector("td:nth-child(1)").textContent.trim();
                const qty = parseFloat(row.querySelector(".qty").value) || 0;
                const rate = parseFloat(row.querySelector(".rate").value) || 0;
                const uom = row.querySelector(".uom").value;
                if (itemCode) {
                    updates[itemCode] = { qty, rate, uom };
                }
            });

            // Step 3: Merge updated fields into existing items
            doc.items.forEach(item => {
                if (updates[item.item_code]) {
                    const update = updates[item.item_code];
                    item.qty = update.qty;
                    item.rate = update.rate;
                    item.uom = update.uom;
                    // Keep other fields (e.g. request_for_quotation) untouched
                }
            });

            // Step 4: Send merged doc to backend
            const saveRes = await frappe.call({
                method: "procurement.api.patch_supplier_quotation",
                args: {
                    name: quotationName,
                    quotation_number: doc.quotation_number,
                    terms: doc.terms,
                    updated_items: doc.items  // Includes qty, rate, uom, item_code
                }
            });

            if (saveRes.message) {
                frappe.msgprint("Quotation updated successfully");
                location.reload();
            }
        } catch (error) {
            frappe.msgprint("Failed to save quotation.");
            console.error(error);
        }
    });

    // Upload Attachment
    document.getElementById("upload-attachment").addEventListener("click", async () => {
        const fileInput = document.getElementById("new-attachment");
        const descriptionInput = document.getElementById("new-attachment-description");

        const file = fileInput.files[0];
        const description = descriptionInput.value || "";

        if (!file) {
            frappe.msgprint("Please select a file to upload.");
            return;
        }

        const formData = new FormData();
        formData.append("file", file);
        formData.append("is_private", "0");
        formData.append("folder", "Home");
        formData.append("doctype", "Supplier Quotation");
        formData.append("docname", quotationName);

        try {
            const res = await fetch("/api/method/upload_file", {
                method: "POST",
                body: formData,
                headers: {
                    "X-Frappe-CSRF-Token": document.querySelector('meta[name="csrf_token"]').getAttribute("content")
                }
            });

            const json = await res.json();

            if (json.message && json.message.file_url) {
                await frappe.call({
                    method: "procurement.api.add_attachment_to_supplier_quotation",
                    args: {
                        quotation: quotationName,
                        file_url: json.message.file_url,
                        description: description
                    }
                });

                frappe.msgprint("Attachment uploaded successfully");
                location.reload();
            } else {
                frappe.msgprint("Upload failed. Please try again.");
                console.error(json);
            }
        } catch (error) {
            frappe.msgprint("Error uploading file.");
            console.error(error);
        }
    });

    // Delete Quotation
    document.getElementById("delete-quotation").addEventListener("click", async () => {
        if (!confirm("Are you sure you want to delete this quotation?")) return;

        try {
            await frappe.call({
                method: "frappe.client.delete",
                args: {
                    doctype: "Supplier Quotation",
                    name: quotationName
                }
            });

            frappe.msgprint("Quotation deleted successfully");
            window.location.href = "/supplier-quotations";
        } catch (error) {
            frappe.msgprint("Failed to delete quotation.");
            console.error(error);
        }
    });

    // Submit Quotation
    document.getElementById("submit-quotation").addEventListener("click", () => {
        frappe.confirm(
            "Once submitted, the quotation is final and cannot be changed.<br><br><b>Do you want to continue?</b>",
            async () => {
                try {
                    // First, fetch the full doc
                    const r = await frappe.call({
                        method: "frappe.client.get",
                        args: {
                            doctype: "Supplier Quotation",
                            name: quotationName
                        }
                    });

                    const doc = r.message;

                    // Then submit it
                    await frappe.call({
                        method: "frappe.client.submit",
                        args: { doc }
                    });

                    frappe.msgprint("Quotation submitted successfully.");
                    location.reload();
                } catch (error) {
                    frappe.msgprint("Failed to submit quotation.");
                    console.error(error);
                }
            },
            () => {
                frappe.msgprint("Submission cancelled.");
            }
        );
    });

    // Live Update of Amount on Qty or Rate Change
    function updateAmountForRow(row) {
        const qty = parseFloat(row.querySelector(".qty").value) || 0;
        const rate = parseFloat(row.querySelector(".rate").value) || 0;
        const amount = qty * rate;
        row.querySelector(".amount").textContent = amount.toFixed(2);
    }

    document.querySelectorAll("#items-table tbody tr").forEach(row => {
        const qtyInput = row.querySelector(".qty");
        const rateInput = row.querySelector(".rate");

        qtyInput.addEventListener("input", () => updateAmountForRow(row));
        rateInput.addEventListener("input", () => updateAmountForRow(row));
    });
});
