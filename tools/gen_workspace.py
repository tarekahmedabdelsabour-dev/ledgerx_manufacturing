"""Writes the workspace, sidebar and dock JSON of ledgerx_manufacturing. Run from the repo root."""
import json
import os
import uuid

BASE = os.path.join(os.path.dirname(__file__), "..", "ledgerx_manufacturing")
TS = "2026-11-19 07:00:00.000000"  # raise this whenever the workspace changes: migrate only re-reads a file that is newer than the saved one
OPEN = ["Open", "Work In Progress", "On Hold", "Material Transferred", "Partially Transferred"]
CARDS = [  # (label, doctype, filters, function, fn_field)
	("Open Job Cards", "Job Card", [["Job Card", "docstatus", "=", 0], ["Job Card", "status", "in", OPEN]], "Count", None),
	("Jobs in Progress", "Job Card", [["Job Card", "status", "=", "Work In Progress"], ["Job Card", "docstatus", "=", 0]], "Count", None),
	("Paused Jobs", "Job Card", [["Job Card", "is_paused", "=", 1], ["Job Card", "docstatus", "=", 0]], "Count", None),
	("Work Orders In Process", "Work Order", [["Work Order", "status", "=", "In Process"]], "Count", None),
	("Work Orders Not Started", "Work Order", [["Work Order", "status", "=", "Not Started"]], "Count", None),
	("Rejected Inspections This Month", "Quality Inspection", [["Quality Inspection", "status", "=", "Rejected"], ["Quality Inspection", "report_date", "Timespan", "this month"]], "Count", None),
	("Scans Today", "Production Scan", [["Production Scan", "scanned_at", "Timespan", "today"]], "Count", None),
	("Scrap Reports Today", "Production Scan", [["Production Scan", "action", "=", "Complete"], ["Production Scan", "scrap_qty", ">", 0], ["Production Scan", "scanned_at", "Timespan", "today"]], "Count", None),
]
CHARTS = [  # (name, doctype, type, kind, extra)
	("Job Cards by Status", "Job Card", "Donut", "group", {"by": "status"}),
	("Work Orders by Status", "Work Order", "Donut", "group", {"by": "status"}),
	("Scans per Day", "Production Scan", "Bar", "series", {"based_on": "scanned_at", "filters": [], "interval": "Daily", "timespan": "Last Month"}),
	("Scrap by Reason", "Production Scan", "Donut", "group", {"by": "waste_reason", "filters": [["Production Scan", "scrap_qty", ">", 0]]}),
]
GROUPS = [  # (title, icon, collapsed, [(label, kind, target, icon)])
	("Production", None, 0, [
		("Operator Screen", "URL", "/factory", "scan-barcode"), ("Work Order", "DocType", "Work Order", "clipboard-list"), ("Job Card", "DocType", "Job Card", "id-card"),
		("Production Plan", "DocType", "Production Plan", "calendar-range"), ("BOM", "DocType", "BOM", "list-tree"), ("Stock Entry", "DocType", "Stock Entry", "package"),
		("Production Scan", "DocType", "Production Scan", "scan-line")]),
	("Quality", "shield-check", 0, [
		("Quality Inspection", "DocType", "Quality Inspection", "clipboard-check"), ("Non Conformance", "DocType", "Non Conformance", "triangle-alert"),
		("Quality Action", "DocType", "Quality Action", "wrench"), ("Quality Goal", "DocType", "Quality Goal", "target"), ("Quality Review", "DocType", "Quality Review", "clipboard-pen"),
		("Quality Feedback", "DocType", "Quality Feedback", "message-square"), ("Quality Meeting", "DocType", "Quality Meeting", "users"),
		("Quality Procedure", "DocType", "Quality Procedure", "workflow"), ("Quality Inspection Template", "DocType", "Quality Inspection Template", "file-check")]),
	("Reports", "bar-chart-3", 0, [
		("Line Efficiency", "Report", "Line Efficiency", "gauge"), ("Waste Report", "Report", "Waste Report", "trash-2"), ("Operator Productivity", "Report", "Operator Productivity", "user-check"),
		("Production Cost", "Report", "Production Cost", "calculator"), ("Work Order Summary", "Report", "Work Order Summary", "layout-list"), ("Job Card Summary", "Report", "Job Card Summary", "layout-list"),
		("Production Analytics", "Report", "Production Analytics", "trending-up"), ("Downtime Analysis", "Report", "Downtime Analysis", "timer"),
		("Quality Inspection Summary", "Report", "Quality Inspection Summary", "clipboard-check")]),
	("Planning and Tools", "calendar-range", 1, [
		("Master Production Schedule", "DocType", "Master Production Schedule", "calendar"), ("Sales Forecast", "DocType", "Sales Forecast", "trending-up"),
		("BOM Creator", "DocType", "BOM Creator", "list-plus"), ("BOM Update Tool", "DocType", "BOM Update Tool", "refresh-cw"), ("Downtime Entry", "DocType", "Downtime Entry", "timer-off")]),
	("Setup", "settings", 1, [
		("Production Line", "DocType", "Production Line", "factory"), ("Workstation", "DocType", "Workstation", "cpu"), ("Workstation Type", "DocType", "Workstation Type", "cpu"),
		("Operation", "DocType", "Operation", "cog"), ("Routing", "DocType", "Routing", "route"), ("Plant Floor", "DocType", "Plant Floor", "layout-grid"),
		("Waste Reason", "DocType", "Waste Reason", "trash"), ("Item", "DocType", "Item", "box"), ("Warehouse", "DocType", "Warehouse", "warehouse"),
		("Factory Settings", "DocType", "Factory Settings", "settings"), ("Manufacturing Settings", "DocType", "Manufacturing Settings", "settings-2")]),
	("Related", "link-2", 1, [
		("Employee", "DocType", "Employee", "user-round"), ("Material Request", "DocType", "Material Request", "package-search"), ("Purchase Order", "DocType", "Purchase Order", "shopping-cart"),
		("Sales Order", "DocType", "Sales Order", "file-text")]),
]
TOP = ["Work Order", "Job Card", "Quality Inspection", "Production Cost"]


def write(path, data):
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "w", encoding="utf-8") as fh:
		json.dump(data, fh, indent=1, ensure_ascii=False)
		fh.write("\n")


def slug(n):
	return n.lower().replace(" ", "_").replace("-", "_")


def write_cards():
	for label, dt, flt, fn, _f in CARDS:
		write(os.path.join(BASE, "factory", "number_card", slug(label), slug(label) + ".json"), {
			"creation": TS, "docstatus": 0, "doctype": "Number Card", "document_type": dt, "filters_json": json.dumps(flt), "function": fn,
			"idx": 0, "is_public": 1, "is_standard": 1, "label": label, "modified": TS, "modified_by": "Administrator", "module": "Factory",
			"name": label, "owner": "Administrator", "show_percentage_stats": 0, "stats_time_interval": "Daily", "type": "Document Type"})
	for name, dt, typ, kind, x in CHARTS:
		d = {"chart_name": name, "creation": TS, "docstatus": 0, "doctype": "Dashboard Chart", "document_type": dt, "dynamic_filters_json": "",
			"idx": 0, "is_public": 1, "is_standard": 1, "modified": TS, "modified_by": "Administrator", "module": "Factory", "name": name,
			"number_of_groups": 0, "owner": "Administrator", "type": typ, "use_report_chart": 0, "y_axis": []}
		if kind == "group":
			d.update({"chart_type": "Group By", "group_by_based_on": x["by"], "group_by_type": "Count", "filters_json": json.dumps(x.get("filters", [])), "timeseries": 0})
		else:
			d.update({"chart_type": "Count", "based_on": x["based_on"], "filters_json": json.dumps(x["filters"]), "time_interval": x.get("interval", "Monthly"),
				"timeseries": 1, "timespan": x.get("timespan", "Last Year")})
		write(os.path.join(BASE, "factory", "dashboard_chart", slug(name), slug(name) + ".json"), d)


def main():
	write_cards()
	rid = lambda: uuid.uuid4().hex[:10]
	content = [{"id": rid(), "type": "header", "data": {"text": '<span class="h4"><b>Factory</b></span>', "col": 12}}]
	for label, *_r in CARDS:
		content.append({"id": rid(), "type": "number_card", "data": {"number_card_name": label, "col": 3}})
	for name, *_r in CHARTS:
		content.append({"id": rid(), "type": "chart", "data": {"chart_name": name, "col": 6}})
	shortcuts, links = [], []
	for label in TOP:
		content.insert(1 + len(shortcuts), {"id": rid(), "type": "shortcut", "data": {"shortcut_name": label, "col": 3}})
		kind = "Report" if label in ("Production Cost",) else "DocType"
		sc = {"label": label, "link_to": label, "type": kind}
		if kind == "DocType":
			sc["doc_view"] = "List"
		else:
			sc["is_query_report"] = 1
		shortcuts.append(sc)
	for title, _i, _c, items in GROUPS[1:]:
		content.append({"id": rid(), "type": "card", "data": {"card_name": title, "col": 4}})
		links.append({"type": "Card Break", "label": title, "hidden": 0, "is_query_report": 0, "link_count": len(items), "onboard": 0})
		for label, kind, target, _icon in items:
			links.append({"type": "Link", "label": label, "link_type": kind, "link_to": target, "hidden": 0, "is_query_report": 1 if kind == "Report" else 0,
				"onboard": 0, "dependencies": "", "only_for": ""})
	write(os.path.join(BASE, "factory", "workspace", "factory", "factory.json"), {
		"charts": [{"chart_name": c[0], "label": c[0]} for c in CHARTS], "content": json.dumps(content), "creation": TS, "custom_blocks": [], "docstatus": 0, "doctype": "Workspace",
		"for_user": "", "hide_custom": 1, "icon": "factory", "idx": 1, "is_hidden": 0, "label": "Factory", "links": links, "title": "Factory", "modified": TS,
		"modified_by": "Administrator", "module": "Factory", "name": "Factory", "number_cards": [{"label": c[0], "number_card_name": c[0]} for c in CARDS], "owner": "Administrator",
		"parent_page": "", "public": 1, "quick_lists": [], "roles": [], "sequence_id": 22.0, "shortcuts": shortcuts})
	def row(i, label, kind, target, icon, child):
		d = {"child": child, "collapsible": 1, "doctype": "Sidebar Item", "icon": icon, "idx": i, "indent": 0, "keep_closed": 0, "label": label,
			"parentfield": "items", "parenttype": "Sidebar", "show_arrow": 0, "type": "Link"}
		if kind == "URL":
			d.update({"link_type": "URL", "url": target, "open_in_new_tab": 1})
		else:
			d.update({"link_to": target, "link_type": kind})
		return d
	items = [row(1, "Home", "Workspace", "Factory", "house", 0)]
	for title, icon, closed, entries in GROUPS:
		if icon:
			items.append({"child": 0, "collapsible": 1, "doctype": "Sidebar Item", "icon": icon, "idx": len(items) + 1, "indent": 1, "keep_closed": closed,
				"label": title, "link_type": "DocType", "parentfield": "items", "parenttype": "Sidebar", "show_arrow": 0, "type": "Section Break"})
		for label, kind, target, ic in entries:
			items.append(row(len(items) + 1, label, kind, target, ic, 1 if icon else 0))
	write(os.path.join(BASE, "sidebar", "factory", "factory.json"), {"app": "ledgerx_factory", "doctype": "Sidebar", "header_icon": "factory",
		"items": items, "module": "Factory", "name": "Factory", "standard": 1, "title": "Factory"})
	write(os.path.join(BASE, "dock", "factory", "factory.json"), {"app": "ledgerx_factory", "creation": TS, "docstatus": 0, "doctype": "Dock", "idx": 0,
		"items": [{"added": 0, "hidden": 0, "icon": "factory", "link_to": "Factory", "link_type": "Sidebar", "title": "Factory"}],
		"modified": TS, "modified_by": "Administrator", "name": "factory", "owner": "Administrator", "standard": 1})


main()
