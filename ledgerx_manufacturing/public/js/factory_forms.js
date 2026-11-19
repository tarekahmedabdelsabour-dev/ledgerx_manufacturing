// Print Barcode Label button on the documents an operator scans, and an Operator Screen shortcut on Job Card.
(function () {
	["Job Card", "Work Order", "Workstation", "Employee", "Item", "Production Line", "Batch"].forEach(function (dt) {
		frappe.ui.form.on(dt, {
			refresh: function (frm) {
				if (frm.is_new()) return;
				frm.add_custom_button(__("Print Barcode Label"), function () {
					window.open("/factory-labels?doctype=" + encodeURIComponent(dt) + "&names=" + encodeURIComponent(frm.doc.name), "_blank");
				}, __("Barcode"));
			},
		});
	});
	frappe.ui.form.on("Job Card", {
		refresh: function (frm) {
			if (frm.is_new() || frm.doc.docstatus !== 0) return;
			frm.add_custom_button(__("Open in Operator Screen"), function () {
				window.open("/factory?code=" + encodeURIComponent(frm.doc.name), "_blank");
			}, __("Barcode"));
		},
	});
	// List views: print labels for the selected rows.
	["Job Card", "Work Order", "Workstation", "Employee", "Item"].forEach(function (dt) {
		var old = (frappe.listview_settings[dt] || {}).onload;
		frappe.listview_settings[dt] = Object.assign(frappe.listview_settings[dt] || {}, {
			onload: function (listview) {
				if (old) old(listview);
				listview.page.add_action_item(__("Print Barcode Labels"), function () {
					var names = listview.get_checked_items(true);
					if (!names.length) { frappe.msgprint(__("Select the rows first.")); return; }
					window.open("/factory-labels?doctype=" + encodeURIComponent(dt) + "&names=" + encodeURIComponent(names.join(",")), "_blank");
				});
			},
		});
	});
})();
