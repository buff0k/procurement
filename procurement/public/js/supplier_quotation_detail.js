// Copyright (c) 2025, Isambane Mining (Pty) Ltd and contributors
// For license information, please see license.txt

frappe.ready(() => {
    const quotationName = document.getElementById("quotation-container").dataset.doc;

    const updateNettTotal = () => {
        let nettTotal = 0;
        document.querySelectorAll("#items-table tbody tr").forEach(row => {
            const qty = parseFloat(row.querySelector(".qty").value) || 0;
            const rate = parseFloat(row.querySelector(".rate").value) || 0;
            const subtotal = qty * rate;
            row.querySelector(".amount").textContent = subtotal.toFixed(2);
            nettTotal += subtotal;
        });
    
        // Update the text content of the Net Total element
        const netTotalContainer = document.getElementById("nett-total-wrapper");
        if (netTotalContainer) {
            netTotalContainer.innerHTML = `
                <strong>Net Total: ${nettTotal.toFixed(2)}</strong><br>
                <em>(Excl. VAT)</em>
            `;
        }
    };

    // Initial calculation
    updateNettTotal();

    // Recalculate Nett Total on changes
    document.querySelectorAll("#items-table").forEach(table => {
        table.addEventListener("input", event => {
            if (event.target.classList.contains("qty") || event.target.classList.contains("rate")) {
                updateNettTotal();
            }
        });
    });

    // Save Quotation
    document.getElementById("save-quotation").addEventListener("click", async () => {
        try {
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

            const updates = {};
            document.querySelectorAll("#items-table tbody tr").forEach(row => {
                const description = row.querySelector("td:nth-child(1)").textContent.trim();
                const qty = parseFloat(row.querySelector(".qty").value) || 0;
                const rate = parseFloat(row.querySelector(".rate").value) || 0;
                const uom = row.querySelector(".uom").value;
                if (description) {
                    updates[description] = { qty, rate, uom };
                }
            });

            doc.items.forEach(item => {
                const key = item.description;
                if (updates[key]) {
                    const update = updates[key];
                    item.qty = update.qty;
                    item.rate = update.rate;
                    item.uom = update.uom;
                }
            });

            const saveRes = await frappe.call({
                method: "procurement.api.patch_supplier_quotation",
                args: {
                    name: quotationName,
                    quotation_number: doc.quotation_number,
                    terms: doc.terms,
                    updated_items: doc.items
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

    // Submit Quotation
    document.getElementById("submit-quotation").addEventListener("click", () => {
        frappe.confirm(
            "Are you sure you want to submit this quotation? <br><br><strong>Once submitted, it can no longer be amended.</strong>",
            async () => {
                try {
                    const { message: doc } = await frappe.call({
                        method: "frappe.client.get",
                        args: {
                            doctype: "Supplier Quotation",
                            name: quotationName
                        }
                    });
    
                    await frappe.call({
                        method: "frappe.client.submit",
                        args: {
                            doc: doc
                        }
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

    // Delete Quotation
    document.getElementById("delete-quotation").addEventListener("click", () => {
        frappe.confirm(
            "Are you sure you want to <strong>permanently delete</strong> this quotation?",
            async () => {
                try {
                    await frappe.call({
                        method: "frappe.client.delete",
                        args: {
                            doctype: "Supplier Quotation",
                            name: quotationName
                        }
                    });
                    frappe.msgprint("Quotation deleted successfully.");
                    window.location.href = "/supplier_quotation_list";
                } catch (error) {
                    frappe.msgprint("Failed to delete quotation.");
                    console.error(error);
                }
            },
            () => {
                frappe.msgprint("Deletion cancelled.");
            }
        );
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
                frappe.msgprint("File uploaded and attached.");
                location.reload();
            } else {
                frappe.msgprint("Failed to upload file.");
            }
        } catch (error) {
            frappe.msgprint("File upload error.");
            console.error(error);
        }
    });
});
