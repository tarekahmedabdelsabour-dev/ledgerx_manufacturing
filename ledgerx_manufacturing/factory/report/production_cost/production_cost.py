import frappe
from frappe import _
from frappe.utils import flt

from ledgerx_manufacturing.engine import logic


def execute(filters=None):
	filters = frappe._dict(filters or {})
	extra = "and se.company = %(company)s" if filters.company else ""
	rows = frappe.db.sql(
		f"""select se.work_order, sum(se.fg_completed_qty) as qty, sum(se.total_outgoing_value) as material, sum(se.total_additional_costs) as operating
		from `tabStock Entry` se
		where se.purpose = 'Manufacture' and se.docstatus = 1 and ifnull(se.work_order, '') != '' and se.posting_date between %(f)s and %(t)s {extra}
		group by se.work_order""", {"f": filters.from_date, "t": filters.to_date, "company": filters.company}, as_dict=True)
	data = []
	for r in rows:
		wo = frappe.db.get_value("Work Order", r.work_order, ["production_item", "item_name", "bom_no"], as_dict=True)
		if not wo or (filters.item_code and wo.production_item != filters.item_code):
			continue
		std = 0.0
		if wo.bom_no:
			b = frappe.db.get_value("BOM", wo.bom_no, ["total_cost", "quantity"], as_dict=True)
			std = flt(b.total_cost) / flt(b.quantity) if b and flt(b.quantity) else 0.0
		actual = logic.unit_cost(r.material, r.operating, r.qty)
		diff, pct = logic.cost_variance(actual, std)
		data.append({"work_order": r.work_order, "item": wo.production_item, "item_name": wo.item_name, "qty": flt(r.qty), "material": flt(r.material), "operating": flt(r.operating),
			"total": flt(r.material) + flt(r.operating), "unit_cost": actual, "std_unit_cost": round(std, 4), "variance": diff, "variance_pct": pct})
	cols = [
		{"label": _("Work Order"), "fieldname": "work_order", "fieldtype": "Link", "options": "Work Order", "width": 140},
		{"label": _("Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 130},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 150},
		{"label": _("Produced Quantity"), "fieldname": "qty", "fieldtype": "Float", "width": 110},
		{"label": _("Material Cost"), "fieldname": "material", "fieldtype": "Currency", "width": 120},
		{"label": _("Operating Cost"), "fieldname": "operating", "fieldtype": "Currency", "width": 120},
		{"label": _("Total Cost"), "fieldname": "total", "fieldtype": "Currency", "width": 120},
		{"label": _("Actual Unit Cost"), "fieldname": "unit_cost", "fieldtype": "Currency", "width": 120},
		{"label": _("Standard Unit Cost (BOM)"), "fieldname": "std_unit_cost", "fieldtype": "Currency", "width": 140},
		{"label": _("Variance"), "fieldname": "variance", "fieldtype": "Currency", "width": 100},
		{"label": _("Variance %"), "fieldname": "variance_pct", "fieldtype": "Percent", "width": 100},
	]
	return cols, data
