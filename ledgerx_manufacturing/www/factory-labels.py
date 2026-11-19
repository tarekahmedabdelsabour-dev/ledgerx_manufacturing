import frappe
from frappe import _

no_cache = 1
sitemap = 0


def _code_and_text(doctype, name):
	"""(barcode value, title, subtitle) of one record."""
	d = frappe.get_doc(doctype, name)
	d.check_permission("read")
	if doctype == "Job Card":
		return d.name, d.production_item or d.name, f"{d.operation or ''} - {d.workstation or ''}  ({d.for_quantity})"
	if doctype == "Work Order":
		return d.name, d.production_item, f"{d.item_name or ''}  ({d.qty})"
	if doctype == "Workstation":
		return d.get("lx_barcode") or d.name, d.name, d.get("lx_production_line") or ""
	if doctype == "Employee":
		return d.get("lx_badge_code") or d.name, d.employee_name, d.designation or d.name
	if doctype == "Item":
		code = frappe.db.get_value("Item Barcode", {"parent": d.name}, "barcode") or d.name
		return code, d.item_name, d.name
	if doctype == "Production Line":
		return d.barcode, d.line_name, d.company or ""
	if doctype == "Batch":
		return d.name, d.item, d.name
	frappe.throw(_("Not supported"))


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/factory-labels"
		raise frappe.Redirect
	form = frappe.form_dict
	doctype = form.get("doctype") or ""
	if doctype not in ("Job Card", "Work Order", "Workstation", "Employee", "Item", "Production Line", "Batch"):
		frappe.throw(_("Not supported"))
	names = [n for n in (form.get("names") or "").split(",") if n][:200]
	context.labels = [dict(zip(("code", "title", "sub"), _code_and_text(doctype, n))) for n in names]
	context.doctype_label = _(doctype)
	context.no_header = 1
	context.show_sidebar = 0
	context.title = _("Barcode Labels")
