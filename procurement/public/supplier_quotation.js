frappe.ready(function () {
  // Attach event listener to the form submit button
  $("form").on("submit", function (e) {
    e.preventDefault(); // Prevent default form submission

    const notes = $("#notes").val();
    const attachments = getAttachments(); // Function to collect attachments

    if (!notes) {
      frappe.msgprint("Please add notes before submitting.");
      return;
    }

    frappe.call({
      method: "my_app.api.supplier_quotation.submit",
      args: {
        notes: notes,
        attachments: attachments,
      },
      callback: function (r) {
        if (r.message) {
          frappe.msgprint(r.message);
          location.reload();
        }
      },
    });
  });

  function getAttachments() {
    // Collect attachment details
    let attachments = [];
    $(".attachment-row").each(function () {
      const desc = $(this).find(".file-desc").val();
      const file = $(this).find(".file-attach")[0].files[0];
      if (desc && file) {
        attachments.push({
          file_desc: desc,
          file: file,
        });
      }
    });
    return attachments;
  }
});
