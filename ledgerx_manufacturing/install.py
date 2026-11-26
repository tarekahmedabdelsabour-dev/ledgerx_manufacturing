"""Install and migrate steps. Each is idempotent and a failing step never aborts a migrate."""
import os

import frappe
from frappe.model.naming import make_autoname

MODULE = "Factory"
ROLES = ["Factory Manager", "Factory Supervisor", "Factory Operator"]
WASTE = [("Material Defect", "Scrap"), ("Machine Fault", "Scrap"), ("Operator Error", "Scrap"), ("Cutting Waste", "Scrap"),
	("Needs Rework", "Rework"), ("Setup Loss", "Setup Loss"), ("Other", "Other")]


def check_app_permission():
	if frappe.session.user == "Administrator":
		return True
	roles = set(frappe.get_roles())
	return bool(roles & set(ROLES + ["System Manager", "Manufacturing Manager", "Manufacturing User", "Quality Manager"]))


def after_install():
	_all()


def after_migrate():
	_all()


def _all():
	for fn in (ensure_module, ensure_roles, ensure_custom_fields, ensure_waste_reasons, ensure_settings, backfill_barcodes, hide_standard_tiles, refresh_workspace):
		try:
			fn()
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title=f"ledgerx_manufacturing install step failed: {fn.__name__}")
	frappe.clear_cache()


def ensure_module():
	if not frappe.db.exists("Module Def", MODULE):
		frappe.get_doc({"doctype": "Module Def", "module_name": MODULE, "app_name": "ledgerx_manufacturing"}).insert(ignore_permissions=True)


def ensure_roles():
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)


FIELDS = [
	("Workstation", "lx_barcode", {"label": "Station Barcode", "fieldtype": "Data", "insert_after": "workstation_name", "no_copy": 1,
		"description": "Printed on the station label. Filled automatically; you may type your own pre-printed code."}),
	("Workstation", "lx_production_line", {"label": "Production Line", "fieldtype": "Link", "options": "Production Line", "insert_after": "lx_barcode", "in_standard_filter": 1}),
	("Employee", "lx_badge_code", {"label": "Badge Barcode", "fieldtype": "Data", "insert_after": "employee_name", "no_copy": 1,
		"description": "Optional. When empty the employee ID is the badge code."}),
	("Job Card", "lx_production_line", {"label": "Production Line", "fieldtype": "Link", "options": "Production Line", "insert_after": "workstation", "read_only": 1, "in_standard_filter": 1}),
]


def ensure_custom_fields():
	for dt, name, spec in FIELDS:
		if frappe.db.exists("DocType", dt) and not frappe.db.exists("Custom Field", {"dt": dt, "fieldname": name}):
			frappe.get_doc({"doctype": "Custom Field", "dt": dt, "fieldname": name, **spec}).insert(ignore_permissions=True)


def ensure_waste_reasons():
	for reason, kind in WASTE:
		if not frappe.db.exists("Waste Reason", reason):
			frappe.get_doc({"doctype": "Waste Reason", "reason": reason, "kind": kind}).insert(ignore_permissions=True)


def ensure_settings():
	s = frappe.get_doc("Factory Settings")
	changed = False
	if not s.company:
		s.company = frappe.db.get_single_value("Global Defaults", "default_company") or frappe.db.get_value("Company", {}, "name")
		changed = bool(s.company)
	if not s.default_waste_reason and frappe.db.exists("Waste Reason", "Other"):
		s.default_waste_reason, changed = "Other", True
	if changed:
		s.flags.ignore_mandatory = True  # the accounts are chosen later, in the settings form
		s.save(ignore_permissions=True)


def backfill_barcodes():
	"""Workstations and lines that existed before the app get their barcode."""
	if frappe.get_meta("Workstation").has_field("lx_barcode"):
		for name in frappe.get_all("Workstation", filters={"lx_barcode": ["is", "not set"]}, pluck="name"):
			frappe.db.set_value("Workstation", name, "lx_barcode", make_autoname("WS-.####"), update_modified=False)
	for name in frappe.get_all("Production Line", filters={"barcode": ["is", "not set"]}, pluck="name"):
		frappe.db.set_value("Production Line", name, "barcode", make_autoname("LN-.####"), update_modified=False)


def hide_standard_tiles():
	"""Manufacturing and Quality now live inside the Factory tile, so the standard ones leave the desktop and the dock."""
	for name in ("Manufacturing", "Quality"):
		if frappe.db.exists("Desktop Icon", name):
			frappe.db.set_value("Desktop Icon", name, "hidden", 1, update_modified=False)
	if frappe.db.exists("DocType", "Dock Item"):
		frappe.db.sql(
			"update `tabDock Item` set hidden=1 where parent=%s and link_to in ('Manufacturing', 'Quality')", ("erpnext",)
		)


def refresh_workspace():
	"""Migrate only re-reads a workspace file that is newer than the saved one: force it."""
	base = os.path.join(frappe.get_app_path("ledgerx_manufacturing"), "factory")
	for dt in ("number_card", "dashboard_chart"):
		folder = os.path.join(base, dt)
		for name in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
			if os.path.isdir(os.path.join(folder, name)):
				frappe.reload_doc("factory", dt, name, force=True)
	frappe.reload_doc("factory", "workspace", "factory", force=True)
