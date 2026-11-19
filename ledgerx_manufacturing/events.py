import frappe
from frappe import _
from frappe.model.naming import make_autoname


def workstation_validate(doc, method=None):
	if doc.meta.has_field("lx_barcode") and not doc.get("lx_barcode"):
		doc.lx_barcode = make_autoname("WS-.####")


def production_line_validate(doc, method=None):
	if not doc.barcode:
		doc.barcode = make_autoname("LN-.####")


def job_card_validate(doc, method=None):
	if doc.meta.has_field("lx_production_line") and doc.workstation:
		doc.lx_production_line = frappe.db.get_value("Workstation", doc.workstation, "lx_production_line")


def job_card_before_submit(doc, method=None):
	"""Optional house rule on top of the per-operation switch: every job card needs an accepted inspection."""
	if not frappe.db.get_single_value("Factory Settings", "require_quality_on_all"):
		return
	qi = doc.quality_inspection
	row = frappe.db.get_value("Quality Inspection", qi, ["status", "docstatus"], as_dict=True) if qi else None
	if not row or row.docstatus != 1 or row.status != "Accepted":
		frappe.throw(_("Job Card {0} needs an accepted Quality Inspection before it can be submitted.").format(doc.name))
