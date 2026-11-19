"""Writes the report JSON stubs; the .py/.js of each report are hand-written next to them."""
import json
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "ledgerx_manufacturing", "factory", "report")
TS = "2026-11-19 06:00:00.000000"
ROLES = ["Factory Manager", "Factory Supervisor", "System Manager", "Manufacturing Manager", "Manufacturing User", "Accounts Manager"]
REPORTS = [("Line Efficiency", "Job Card"), ("Waste Report", "Production Scan"), ("Operator Productivity", "Job Card"), ("Production Cost", "Work Order")]

for name, ref in REPORTS:
	slug = name.lower().replace(" ", "_")
	folder = os.path.join(BASE, slug)
	os.makedirs(folder, exist_ok=True)
	open(os.path.join(folder, "__init__.py"), "a").close()
	with open(os.path.join(folder, slug + ".json"), "w", encoding="utf-8") as fh:
		json.dump({"add_total_row": 0, "creation": TS, "disabled": 0, "docstatus": 0, "doctype": "Report", "idx": 0, "is_standard": "Yes", "modified": TS,
			"modified_by": "Administrator", "module": "Factory", "name": name, "owner": "Administrator", "prepared_report": 0, "ref_doctype": ref,
			"report_name": name, "report_type": "Script Report", "roles": [{"role": r} for r in ROLES]}, fh, indent=1)
		fh.write("\n")
