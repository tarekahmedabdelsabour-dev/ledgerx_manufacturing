"""Builds every DocType JSON of ledgerx_manufacturing from the compact table below.
Run from the repo root:  python3 tools/gen_doctypes.py   (rewrites ledgerx_manufacturing/factory/doctype/*)"""
import json
import os
import re

ROOT = os.path.join(os.path.dirname(__file__), "..", "ledgerx_manufacturing", "factory", "doctype")
TS = "2026-11-16 08:00:00.000000"
MODULE = "Factory"

MGR, SUP, OPR = "Factory Manager", "Factory Supervisor", "Factory Operator"


def f(name, ftype, label=None, **kw):
	d = {"fieldname": name, "fieldtype": ftype}
	if ftype not in ("Section Break", "Column Break", "Tab Break"):
		d["label"] = label or name.replace("_", " ").title()
	elif label:
		d["label"] = label
	d.update(kw)
	return d


def sec(name, label=None, **kw):
	return f(name, "Section Break", label, **kw)


def col(name):
	return f(name, "Column Break")


def perms(*rows):
	out = []
	for role, mode in rows:
		p = {"role": role, "read": 1, "report": 1, "print": 1, "export": 1}
		if mode in ("rw", "rwc", "all"):
			p["write"] = 1
		if mode in ("rwc", "all"):
			p["create"] = 1
		if mode == "all":
			p["delete"] = 1
		out.append(p)
	out.append({"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "report": 1, "print": 1, "export": 1})
	return out


DT = {}


def doctype(name, fields, **kw):
	DT[name] = {"name": name, "fields": fields, **kw}


doctype("Factory Settings", [
	f("company", "Link", "Company", options="Company"),
	sec("sb_scan", "Scanning"),
	f("require_employee_scan", "Check", "Operator Must Scan a Badge", default=0, description="When on, starting a job from the mobile screen needs a scanned employee badge. Off: the signed-in user's employee is used."),
	f("require_station_scan", "Check", "Operator Must Scan the Station", default=0, description="When on, a job can only be started after the station barcode was scanned."),
	f("auto_submit_on_complete", "Check", "Submit the Job Card When the Whole Quantity Is Done", default=1),
	col("cb1"),
	f("default_waste_reason", "Link", "Default Waste Reason", options="Waste Reason"),
	f("scan_sound", "Check", "Beep on Every Scan", default=1),
	sec("sb_q", "Quality"),
	f("require_quality_on_all", "Check", "Every Job Card Needs an Accepted Quality Inspection", default=0, description="Added to the per-operation switch of the standard Work Order: a Job Card cannot be submitted before an accepted inspection exists."),
], issingle=1, icon="fa fa-industry", perms=perms((MGR, "rw")))

doctype("Waste Reason", [
	f("reason", "Data", "Reason", reqd=1, unique=1, in_list_view=1),
	f("kind", "Select", "Kind", options="Scrap\nRework\nSetup Loss\nOther", default="Scrap", in_list_view=1, in_standard_filter=1),
	f("description", "Small Text", "Description"),
], autoname="field:reason", icon="fa fa-trash-o", perms=perms((MGR, "all"), (SUP, "rw"), (OPR, "r")))

doctype("Production Line Station", [
	f("workstation", "Link", "Workstation", options="Workstation", reqd=1, in_list_view=1),
	f("sequence", "Int", "Sequence", in_list_view=1),
	f("barcode", "Data", "Station Barcode", fetch_from="workstation.lx_barcode", read_only=1, in_list_view=1),
], istable=1)

doctype("Production Line", [
	f("line_name", "Data", "Line Name", reqd=1, unique=1, in_list_view=1),
	f("company", "Link", "Company", options="Company", in_standard_filter=1),
	f("plant_floor", "Link", "Plant Floor", options="Plant Floor"),
	col("cb1"),
	f("supervisor", "Link", "Supervisor", options="Employee"),
	f("target_per_hour", "Float", "Target Output per Hour", description="Used by the Line Efficiency report."),
	f("barcode", "Data", "Line Barcode", read_only=1, in_list_view=1),
	f("disabled", "Check", "Disabled"),
	sec("sb_st", "Stations"),
	f("stations", "Table", "Stations", options="Production Line Station"),
	f("notes", "Small Text", "Notes"),
], autoname="field:line_name", title_field="line_name", icon="fa fa-tasks", perms=perms((MGR, "all"), (SUP, "rw"), (OPR, "r")))

doctype("Production Scan", [
	f("scanned_at", "Datetime", "Scanned At", read_only=1, in_list_view=1),
	f("action", "Select", "Action", options="Scan\nStart\nPause\nResume\nComplete\nMaterial Issued\nProduct Received\nQuality Check", read_only=1, in_list_view=1, in_standard_filter=1),
	f("user", "Link", "User", options="User", read_only=1),
	f("employee", "Link", "Employee", options="Employee", read_only=1, in_standard_filter=1),
	col("cb1"),
	f("job_card", "Link", "Job Card", options="Job Card", read_only=1, in_list_view=1),
	f("work_order", "Link", "Work Order", options="Work Order", read_only=1, in_standard_filter=1),
	f("operation", "Link", "Operation", options="Operation", read_only=1),
	f("workstation", "Link", "Workstation", options="Workstation", read_only=1, in_standard_filter=1),
	f("production_line", "Link", "Production Line", options="Production Line", read_only=1, in_standard_filter=1),
	sec("sb_q", "Quantity"),
	f("item_code", "Link", "Item", options="Item", read_only=1),
	f("batch_no", "Data", "Batch", read_only=1),
	f("qty", "Float", "Quantity", read_only=1, in_list_view=1),
	col("cb2"),
	f("scrap_qty", "Float", "Scrap Quantity", read_only=1, in_list_view=1),
	f("waste_reason", "Link", "Waste Reason", options="Waste Reason", read_only=1),
	f("stock_entry", "Link", "Stock Entry", options="Stock Entry", read_only=1),
	f("note", "Small Text", "Note", read_only=1),
], autoname="format:PSC-{#######}", title_field="job_card", icon="fa fa-barcode", perms=perms((MGR, "r"), (SUP, "r")))

def build():
	os.makedirs(ROOT, exist_ok=True)
	for name, d in DT.items():
		fields = d["fields"]
		order = [x["fieldname"] for x in fields]
		istable = d.get("istable", 0)
		out = {
			"actions": [], "creation": TS, "doctype": "DocType", "engine": "InnoDB", "field_order": order, "fields": fields,
			"links": [], "modified": TS, "modified_by": "Administrator", "module": MODULE, "name": name, "owner": "Administrator",
			"sort_field": "creation", "sort_order": "DESC", "states": [],
			"permissions": [] if istable else d.get("perms", []),
		}
		for k in ("autoname", "title_field", "icon", "track_changes", "issingle", "istable", "show_title_field_in_link", "search_fields"):
			if k in d:
				out[k] = d[k]
		if "autoname" not in d and not istable and not d.get("issingle"):
			out["autoname"] = "hash"
		out["allow_rename"] = 0
		slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
		folder = os.path.join(ROOT, slug)
		os.makedirs(folder, exist_ok=True)
		open(os.path.join(folder, "__init__.py"), "a").close()
		with open(os.path.join(folder, slug + ".json"), "w", encoding="utf-8") as fh:
			json.dump(out, fh, indent=1, ensure_ascii=False)
			fh.write("\n")
		py = os.path.join(folder, slug + ".py")
		if not os.path.exists(py):
			cls = "".join(w.capitalize() for w in re.split(r"[^A-Za-z0-9]+", name))
			with open(py, "w") as fh:
				fh.write(f"from frappe.model.document import Document\n\n\nclass {cls}(Document):\n\tpass\n")


if __name__ == "__main__":
	build()
	print(len(DT), "doctypes")
