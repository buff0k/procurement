frappe.call({
    method: "procurement.api.get_supplier_quotations",
    callback: function (r) {
        const container = document.getElementById("quotation-list");
        r.message.forEach(q => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td><a href="/supplier-quotations/${q.name}">${q.name}</a></td>
                <td>${q.quotation_number || ""}</td>
                <td>${q.transaction_date}</td>
                <td>${format_currency(q.grand_total, q.currency)}</td>
            `;
            container.appendChild(row);
        });
    }
});
