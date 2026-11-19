import frappe
from frappe import _

from ledgerx_manufacturing.engine import logic


def execute(filters=None):
	filters = frappe._dict(filters or {})
	cond = {"action": "Complete", "scrap_qty": [">", 0], "scanned_at": ["between", [f"{filters.from_date} 00:00:00", f"{filters.to_date} 23:59:59"]]}
	for k in ("workstation", "production_line", "waste_reason", "item_code"):
		if filters.get(k):
			cond[k] = filters[k]
	data = frappe.get_all("Production Scan", filters=cond, fields=["scanned_at", "job_card", "item_code", "workstation", "production_line", "waste_reason", "scrap_qty", "qty", "employee"], order_by="scanned_at desc")
	for d in data:
		d["scrap_pct"] = logic.scrap_pct(d["qty"], d["scrap_qty"])
	cols = [
		{"label": _("Date"), "fieldname": "scanned_at", "fieldtype": "Datetime", "width": 150},
		{"label": _("Job Card"), "fieldname": "job_card", "fieldtype": "Link", "options": "Job Card", "width": 130},
		{"label": _("Item"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 140},
		{"label": _("Workstation"), "fieldname": "workstation", "fieldtype": "Link", "options": "Workstation", "width": 130},
		{"label": _("Production Line"), "fieldname": "production_line", "fieldtype": "Link", "options": "Production Line", "width": 130},
		{"label": _("Waste Reason"), "fieldname": "waste_reason", "fieldtype": "Link", "options": "Waste Reason", "width": 130},
		{"label": _("Scrap Quantity"), "fieldname": "scrap_qty", "fieldtype": "Float", "width": 110},
		{"label": _("Good Quantity"), "fieldname": "qty", "fieldtype": "Float", "width": 110},
		{"label": _("Scrap %"), "fieldname": "scrap_pct", "fieldtype": "Percent", "width": 90},
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
	]
	by = {}
	for d in data:
		by[d.waste_reason or _("Not specified")] = by.get(d.waste_reason or _("Not specified"), 0) + d.scrap_qty
	chart = {"data": {"labels": list(by), "datasets": [{"name": _("Scrap Quantity"), "values": list(by.values())}]}, "type": "pie"} if by else None
	return cols, data, None, chart
