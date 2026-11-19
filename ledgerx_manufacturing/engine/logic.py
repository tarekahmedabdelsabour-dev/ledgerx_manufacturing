"""Pure rules of the factory module: no database, so they can be unit-tested anywhere."""


def flt(v, p=6):
	try:
		return round(float(v or 0), p)
	except (TypeError, ValueError):
		return 0.0


def clean_code(code):
	"""Scanners add CR/LF, tabs or spaces; some prefix a symbology id. Return the bare value."""
	if code is None:
		return ""
	code = str(code).replace("\r", "").replace("\n", "").replace("\t", "").strip()
	return code


def split_qty(code):
	"""'ITEM-001*12' -> ('ITEM-001', 12.0). A plain code gives quantity 1."""
	code = clean_code(code)
	if "*" in code:
		head, _, tail = code.rpartition("*")
		q = flt(tail)
		if head and q > 0:
			return head, q
	return code, 1.0


def cycle_split(job_qty, done_so_far, loss_so_far, good, scrap):
	"""Split what an operator reports into the numbers the Job Card needs.

	Returns (pending_after, for_quantity) where for_quantity = good + scrap + pending_after, which is the
	rule the standard completion check enforces. Raises ValueError for impossible input."""
	good, scrap = flt(good), flt(scrap)
	if good < 0 or scrap < 0:
		raise ValueError("negative")
	remaining = flt(job_qty) - flt(done_so_far) - flt(loss_so_far)
	if good + scrap > remaining + 1e-9:
		raise ValueError("over")
	pending = max(remaining - good - scrap, 0.0)
	return flt(pending), flt(good + scrap + pending)


def scrap_pct(good, scrap):
	total = flt(good) + flt(scrap)
	return round(flt(scrap) / total * 100, 2) if total else 0.0


def efficiency(produced, hours, target_per_hour):
	"""Units per hour and percent of the target (0 when no target is set)."""
	hours = flt(hours)
	uph = round(flt(produced) / hours, 2) if hours else 0.0
	pct = round(uph / flt(target_per_hour) * 100, 1) if flt(target_per_hour) else 0.0
	return uph, pct


def unit_cost(material, operating, qty):
	qty = flt(qty)
	return round((flt(material) + flt(operating)) / qty, 4) if qty else 0.0


def cost_variance(actual_unit, standard_unit):
	"""(amount, percent) of actual versus standard; positive = more expensive than planned."""
	diff = round(flt(actual_unit) - flt(standard_unit), 4)
	pct = round(diff / flt(standard_unit) * 100, 1) if flt(standard_unit) else 0.0
	return diff, pct


def outstanding(required, issued):
	return round(max(flt(required) - flt(issued), 0.0), 6)


def issue_limit(required, already, qty, tolerance_pct=0):
	"""May this scan be accepted? False when it would pass the required quantity (plus tolerance)."""
	return flt(already) + flt(qty) <= flt(required) * (1 + flt(tolerance_pct) / 100.0) + 1e-9


def next_status(is_paused, has_open_log, pending):
	"""Which buttons the operator sees: a list of actions in screen order."""
	if is_paused:
		return ["resume", "finish"]
	if has_open_log:
		return ["pause", "finish"]
	return ["start"] if flt(pending) > 0 else []
