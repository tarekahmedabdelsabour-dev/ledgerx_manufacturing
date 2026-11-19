import frappe
from frappe import _

from ledgerx_manufacturing.engine import logic


def execute(filters=None):
	filters = frappe._dict(filters or {})
	extra = "and tl.employee = %(employee)s" if filters.employee else ""
	data = frappe.db.sql(
		f"""select tl.employee, e.employee_name, count(distinct tl.parent) as jobs, sum(tl.completed_qty) as good,
			sum(tl.process_loss_qty) as scrap, sum(tl.time_in_mins) / 60 as hours
		from `tabJob Card Time Log` tl
		join `tabJob Card` jc on jc.name = tl.parent
		left join `tabEmployee` e on e.name = tl.employee
		where jc.docstatus < 2 and ifnull(tl.employee, '') != '' and tl.from_time between %(f)s and %(t)s {extra}
		group by tl.employee, e.employee_name order by good desc""",
		{"f": f"{filters.from_date} 00:00:00", "t": f"{filters.to_date} 23:59:59", "employee": filters.employee}, as_dict=True)
	for d in data:
		d["hours"] = round(d["hours"] or 0, 2)
		d["scrap_pct"] = logic.scrap_pct(d["good"], d["scrap"])
		d["uph"], _pct = logic.efficiency(d["good"], d["hours"], 0)
	cols = [
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 170},
		{"label": _("Job Cards"), "fieldname": "jobs", "fieldtype": "Int", "width": 90},
		{"label": _("Good Quantity"), "fieldname": "good", "fieldtype": "Float", "width": 110},
		{"label": _("Scrap Quantity"), "fieldname": "scrap", "fieldtype": "Float", "width": 110},
		{"label": _("Scrap %"), "fieldname": "scrap_pct", "fieldtype": "Percent", "width": 90},
		{"label": _("Hours"), "fieldname": "hours", "fieldtype": "Float", "width": 80},
		{"label": _("Units per Hour"), "fieldname": "uph", "fieldtype": "Float", "width": 110},
	]
	return cols, data
