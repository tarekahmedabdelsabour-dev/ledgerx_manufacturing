import frappe
from frappe import _
from frappe.utils import flt

from ledgerx_manufacturing.engine import logic


def execute(filters=None):
	filters = frappe._dict(filters or {})
	cond = {"docstatus": ["<", 2], "posting_date": ["between", [filters.from_date, filters.to_date]]}
	if filters.company:
		cond["company"] = filters.company
	if filters.production_line:
		cond["lx_production_line"] = filters.production_line
	rows = frappe.get_all("Job Card", filters=cond, fields=["workstation", "lx_production_line", "total_completed_qty", "process_loss_qty", "total_time_in_mins"])
	targets = {r.name: flt(r.target_per_hour) for r in frappe.get_all("Production Line", fields=["name", "target_per_hour"])}
	agg = {}
	for r in rows:
		k = (r.lx_production_line or "", r.workstation or "")
		a = agg.setdefault(k, {"jobs": 0, "good": 0.0, "scrap": 0.0, "mins": 0.0})
		a["jobs"] += 1
		a["good"] += flt(r.total_completed_qty)
		a["scrap"] += flt(r.process_loss_qty)
		a["mins"] += flt(r.total_time_in_mins)
	data = []
	for (line, ws), a in sorted(agg.items()):
		uph, pct = logic.efficiency(a["good"], a["mins"] / 60.0, targets.get(line, 0))
		data.append({"line": line, "workstation": ws, "jobs": a["jobs"], "good": a["good"], "scrap": a["scrap"], "scrap_pct": logic.scrap_pct(a["good"], a["scrap"]),
			"hours": round(a["mins"] / 60.0, 2), "uph": uph, "target": targets.get(line, 0), "eff": pct})
	cols = [
		{"label": _("Production Line"), "fieldname": "line", "fieldtype": "Link", "options": "Production Line", "width": 150},
		{"label": _("Workstation"), "fieldname": "workstation", "fieldtype": "Link", "options": "Workstation", "width": 150},
		{"label": _("Job Cards"), "fieldname": "jobs", "fieldtype": "Int", "width": 90},
		{"label": _("Good Quantity"), "fieldname": "good", "fieldtype": "Float", "width": 110},
		{"label": _("Scrap Quantity"), "fieldname": "scrap", "fieldtype": "Float", "width": 110},
		{"label": _("Scrap %"), "fieldname": "scrap_pct", "fieldtype": "Percent", "width": 90},
		{"label": _("Hours"), "fieldname": "hours", "fieldtype": "Float", "width": 80},
		{"label": _("Units per Hour"), "fieldname": "uph", "fieldtype": "Float", "width": 110},
		{"label": _("Target per Hour"), "fieldname": "target", "fieldtype": "Float", "width": 110},
		{"label": _("Efficiency %"), "fieldname": "eff", "fieldtype": "Percent", "width": 110},
	]
	chart = {"data": {"labels": [d["workstation"] or d["line"] for d in data], "datasets": [{"name": _("Units per Hour"), "values": [d["uph"] for d in data]}]}, "type": "bar"} if data else None
	return cols, data, None, chart
