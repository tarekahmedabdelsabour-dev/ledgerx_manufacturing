frappe.query_reports["Waste Report"] = {
	filters: [
		{ fieldname: "from_date", label: __("From Date"), fieldtype: "Date", reqd: 1, default: frappe.datetime.month_start() },
		{ fieldname: "to_date", label: __("To Date"), fieldtype: "Date", reqd: 1, default: frappe.datetime.get_today() },
		{ fieldname: "production_line", label: __("Production Line"), fieldtype: "Link", options: "Production Line" },
		{ fieldname: "workstation", label: __("Workstation"), fieldtype: "Link", options: "Workstation" },
		{ fieldname: "waste_reason", label: __("Waste Reason"), fieldtype: "Link", options: "Waste Reason" },
		{ fieldname: "item_code", label: __("Item"), fieldtype: "Link", options: "Item" },
	],
};
