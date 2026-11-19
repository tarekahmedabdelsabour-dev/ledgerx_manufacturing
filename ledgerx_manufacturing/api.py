"""Scan API used by the operator screen (/factory) and the desk buttons.

Every function is a thin layer over the standard Job Card / Work Order / Stock Entry documents: the
standard methods do the real work and their own validations, this module only resolves a scanned code,
calls them and keeps a Production Scan log."""
import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime

from ledgerx_manufacturing.engine import logic

OPEN_STATUSES = ("Open", "Work In Progress", "On Hold", "Material Transferred", "Partially Transferred", "To Manufacture")


def settings():
	return frappe.get_cached_doc("Factory Settings")


# ---------------------------------------------------------------- scan resolving

@frappe.whitelist()
def resolve(code):
	"""What did the operator scan? -> {type, name, label, ...}; type is None when unknown."""
	code, qty = logic.split_qty(code)
	if not code:
		return {"type": None}
	if frappe.db.exists("Job Card", code):
		return {"type": "Job Card", "name": code, "label": code}
	if frappe.db.exists("Work Order", code):
		return {"type": "Work Order", "name": code, "label": code}
	line = frappe.db.get_value("Production Line", {"barcode": code}, ["name", "line_name"], as_dict=True)
	if line:
		return {"type": "Production Line", "name": line.name, "label": line.line_name}
	ws = frappe.db.get_value("Workstation", {"lx_barcode": code}, "name") or (code if frappe.db.exists("Workstation", code) else None)
	if ws:
		return {"type": "Workstation", "name": ws, "label": ws}
	emp = _employee_from_code(code)
	if emp:
		return {"type": "Employee", "name": emp.name, "label": emp.employee_name}
	item = _item_from_code(code)
	if item:
		return {"type": "Item", "name": item, "label": frappe.db.get_value("Item", item, "item_name") or item, "qty": qty,
			"batch_no": code if frappe.db.exists("Batch", code) else None}
	return {"type": None, "code": code}


def _employee_from_code(code):
	for field in ("name", "lx_badge_code", "attendance_device_id"):
		if frappe.get_meta("Employee").has_field(field) or field == "name":
			row = frappe.db.get_value("Employee", {field: code, "status": "Active"}, ["name", "employee_name"], as_dict=True)
			if row:
				return row
	return None


def _item_from_code(code):
	item = frappe.db.get_value("Item Barcode", {"barcode": code}, "parent")
	if item:
		return item
	if frappe.db.exists("Item", code):
		return code
	return frappe.db.get_value("Batch", code, "item") if frappe.db.exists("Batch", code) else None


def _operator(employee=None):
	if employee:
		return employee
	if settings().require_employee_scan:
		frappe.throw(_("Scan your employee badge first."))
	return frappe.db.get_value("Employee", {"user_id": frappe.session.user, "status": "Active"}, "name")


def _line_of(workstation):
	return frappe.db.get_value("Workstation", workstation, "lx_production_line") if workstation else None


def _log(action, **kw):
	doc = frappe.get_doc({"doctype": "Production Scan", "action": action, "scanned_at": now_datetime(), "user": frappe.session.user, **kw})
	doc.insert(ignore_permissions=True)
	return doc


# ---------------------------------------------------------------- job cards

def _jc(name, perm="read"):
	doc = frappe.get_doc("Job Card", name)
	doc.check_permission(perm)
	return doc


def _overview(jc):
	open_logs = [r for r in jc.time_logs if r.from_time and not r.to_time]
	pending = flt(jc.for_quantity) - flt(jc.total_completed_qty) - flt(jc.process_loss_qty)
	qi = jc.quality_inspection
	qi_status = frappe.db.get_value("Quality Inspection", qi, ["status", "docstatus"], as_dict=True) if qi else None
	required = bool(frappe.db.get_value("Work Order Operation", jc.operation_id, "quality_inspection_required")) if jc.operation_id else False
	return {
		"name": jc.name, "status": jc.status, "docstatus": jc.docstatus, "is_paused": cint(jc.is_paused),
		"item": jc.production_item, "item_name": jc.item_name, "operation": jc.operation, "workstation": jc.workstation,
		"line": _line_of(jc.workstation), "work_order": jc.work_order, "for_quantity": flt(jc.for_quantity),
		"done": flt(jc.total_completed_qty), "loss": flt(jc.process_loss_qty), "pending": max(pending, 0.0),
		"minutes": flt(jc.total_time_in_mins), "operators": [r.employee for r in open_logs if r.employee],
		"actions": logic.next_status(cint(jc.is_paused), bool(open_logs), max(pending, 0.0)) if jc.docstatus == 0 else [],
		"quality_required": required or cint(settings().require_quality_on_all), "quality_inspection": qi,
		"quality_status": (qi_status.status if qi_status and qi_status.docstatus == 1 else ("Draft" if qi else None)),
	}


@frappe.whitelist()
def job(job_card):
	return _overview(_jc(job_card))


@frappe.whitelist()
def station_jobs(workstation):
	rows = frappe.get_all("Job Card", filters={"workstation": workstation, "docstatus": 0, "status": ["in", OPEN_STATUSES]},
		fields=["name"], order_by="creation asc", limit=30)
	return [_overview(_jc(r.name)) for r in rows]


@frappe.whitelist()
def line_stations(production_line):
	line = frappe.get_doc("Production Line", production_line)
	return [{"workstation": r.workstation, "sequence": r.sequence, "open_jobs": frappe.db.count("Job Card", {"workstation": r.workstation, "docstatus": 0, "status": ["in", OPEN_STATUSES]})}
		for r in sorted(line.stations, key=lambda x: cint(x.sequence))]


@frappe.whitelist()
def start(job_card, employee=None):
	jc = _jc(job_card, "write")
	emp = _operator(employee)
	if cint(jc.is_paused):
		frappe.throw(_("This job is paused: resume it."))
	jc.start_timer(start_time=now_datetime(), employees=[{"employee": emp}] if emp else [])
	_log("Start", job_card=jc.name, work_order=jc.work_order, operation=jc.operation, workstation=jc.workstation,
		production_line=_line_of(jc.workstation), employee=emp, item_code=jc.production_item)
	return _overview(_jc(job_card))


@frappe.whitelist()
def pause(job_card, employee=None):
	jc = _jc(job_card, "write")
	jc.pause_job(end_time=now_datetime())
	_log("Pause", job_card=jc.name, work_order=jc.work_order, workstation=jc.workstation, production_line=_line_of(jc.workstation), employee=employee)
	return _overview(_jc(job_card))


@frappe.whitelist()
def resume(job_card, employee=None):
	jc = _jc(job_card, "write")
	jc.resume_job(start_time=now_datetime())
	_log("Resume", job_card=jc.name, work_order=jc.work_order, workstation=jc.workstation, production_line=_line_of(jc.workstation), employee=employee)
	return _overview(_jc(job_card))


@frappe.whitelist()
def finish(job_card, qty, scrap=0, reason=None, employee=None):
	"""Report good and scrap quantity. The Job Card is submitted when the whole quantity is done."""
	jc = _jc(job_card, "write")
	if not jc.time_logs:
		frappe.throw(_("Start the job before finishing it."))
	try:
		pending, for_qty = logic.cycle_split(jc.for_quantity, jc.total_completed_qty, jc.process_loss_qty, qty, scrap)
	except ValueError as e:
		frappe.throw(_("The reported quantity is more than what is left on this job.") if str(e) == "over" else _("Quantities cannot be negative."))
	good, scrap = flt(qty), flt(scrap)
	if scrap and not reason:
		reason = settings().default_waste_reason
	has_open = any(r.from_time and not r.to_time for r in jc.time_logs)
	args = dict(qty=good, for_quantity=for_qty, pending_qty=pending, process_loss_qty=scrap)
	if has_open:
		args["end_time"] = now_datetime()
	jc.complete_job_card(**args)
	_log("Complete", job_card=jc.name, work_order=jc.work_order, operation=jc.operation, workstation=jc.workstation,
		production_line=_line_of(jc.workstation), employee=employee, item_code=jc.production_item, qty=good, scrap_qty=scrap,
		waste_reason=reason if scrap else None)
	out = {"submitted": False, "message": None}
	if pending == 0 and cint(settings().auto_submit_on_complete):
		fresh = _jc(job_card, "submit")
		try:
			fresh.submit()
			out["submitted"] = True
		except Exception as e:  # typically: quality inspection missing or rejected
			frappe.db.rollback()
			out["message"] = str(e)
			out["needs_quality"] = "uality" in str(e)
	out["job"] = _overview(_jc(job_card))
	return out


@frappe.whitelist()
def quality(job_card):
	"""Open (or create) the In Process quality inspection of a job card."""
	jc = _jc(job_card, "write")
	if jc.quality_inspection:
		return {"name": jc.quality_inspection, "created": False}
	qi = frappe.new_doc("Quality Inspection")
	qi.update({"inspection_type": "In Process", "reference_type": "Job Card", "reference_name": jc.name, "item_code": jc.production_item,
		"sample_size": 1, "inspected_by": frappe.session.user, "quality_inspection_template": jc.quality_inspection_template,
		"batch_no": jc.batch_no})
	qi.get_item_specification_details()
	qi.insert()
	jc.db_set("quality_inspection", qi.name)
	_log("Quality Check", job_card=jc.name, work_order=jc.work_order, workstation=jc.workstation, note=qi.name)
	return {"name": qi.name, "created": True}


# ---------------------------------------------------------------- materials and product (work order level)

def _wo(name, perm="read"):
	doc = frappe.get_doc("Work Order", name)
	doc.check_permission(perm)
	return doc


def _scanned(work_order):
	"""Quantity scanned per item that is not yet on a Stock Entry."""
	rows = frappe.get_all("Production Scan", filters={"work_order": work_order, "action": "Material Issued", "stock_entry": ["is", "not set"]},
		fields=["item_code", "qty"])
	out = {}
	for r in rows:
		out[r.item_code] = out.get(r.item_code, 0.0) + flt(r.qty)
	return out


@frappe.whitelist()
def work_order(work_order):
	wo = _wo(work_order)
	scanned = _scanned(wo.name)
	return {
		"name": wo.name, "status": wo.status, "item": wo.production_item, "item_name": wo.item_name, "qty": flt(wo.qty),
		"produced": flt(wo.produced_qty), "docstatus": wo.docstatus,
		"items": [{"item_code": r.item_code, "item_name": r.item_name, "required": flt(r.required_qty), "transferred": flt(r.transferred_qty),
			"scanned": flt(scanned.get(r.item_code)), "uom": r.stock_uom} for r in wo.required_items],
		"job_cards": frappe.get_all("Job Card", filters={"work_order": wo.name, "docstatus": ["<", 2]}, fields=["name", "operation", "workstation", "status"], order_by="sequence_id asc, creation asc"),
	}


@frappe.whitelist()
def issue_material(work_order, code, qty=1):
	"""Scan a raw material for a work order. Nothing is posted yet: post_issue() creates the Stock Entry."""
	wo = _wo(work_order, "write")
	code, scan_qty = logic.split_qty(code)
	qty = flt(qty) if flt(qty) != 1 else scan_qty
	item = _item_from_code(code)
	if not item:
		frappe.throw(_("Unknown barcode: {0}").format(code))
	row = next((r for r in wo.required_items if r.item_code == item), None)
	if not row:
		frappe.throw(_("{0} is not a material of this work order.").format(item))
	already = flt(row.transferred_qty) + flt(_scanned(wo.name).get(item))
	if not logic.issue_limit(row.required_qty, already, qty):
		frappe.throw(_("{0}: more than the required {1} (already {2}).").format(item, flt(row.required_qty), already))
	_log("Material Issued", work_order=wo.name, item_code=item, qty=qty, batch_no=code if frappe.db.exists("Batch", code) else None)
	return {"item_code": item, "item_name": row.item_name, "required": flt(row.required_qty), "scanned": already + qty - flt(row.transferred_qty), "transferred": flt(row.transferred_qty)}


@frappe.whitelist()
def post_issue(work_order):
	"""Turn the scanned materials into a submitted 'Material Transfer for Manufacture' Stock Entry."""
	from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry

	wo = _wo(work_order, "write")
	scanned = _scanned(wo.name)
	if not scanned:
		frappe.throw(_("Nothing was scanned."))
	se = frappe.get_doc(make_stock_entry(wo.name, "Material Transfer for Manufacture"))
	keep = []
	for row in se.items:
		q = scanned.get(row.item_code)
		if q:
			row.qty = q
			row.transfer_qty = flt(q) * flt(row.conversion_factor or 1)
			keep.append(row)
	se.set("items", keep)
	se.insert()
	se.submit()
	for name in frappe.get_all("Production Scan", filters={"work_order": wo.name, "action": "Material Issued", "stock_entry": ["is", "not set"]}, pluck="name"):
		frappe.db.set_value("Production Scan", name, "stock_entry", se.name, update_modified=False)
	return {"stock_entry": se.name}


@frappe.whitelist()
def receive_product(work_order, qty):
	"""Book the finished product: a submitted 'Manufacture' Stock Entry for `qty`."""
	from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry

	wo = _wo(work_order, "write")
	qty = flt(qty)
	if qty <= 0:
		frappe.throw(_("Enter the quantity."))
	se = frappe.get_doc(make_stock_entry(wo.name, "Manufacture", qty))
	se.insert()
	se.submit()
	_log("Product Received", work_order=wo.name, item_code=wo.production_item, qty=qty, stock_entry=se.name)
	return {"stock_entry": se.name}


@frappe.whitelist()
def recent(limit=15):
	return frappe.get_all("Production Scan", filters={"user": frappe.session.user}, fields=["name", "scanned_at", "action", "job_card", "work_order", "item_code", "qty", "scrap_qty"],
		order_by="scanned_at desc", limit=cint(limit) or 15)
