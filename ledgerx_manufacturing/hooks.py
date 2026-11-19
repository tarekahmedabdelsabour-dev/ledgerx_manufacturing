app_name = "ledgerx_manufacturing"
app_title = "Factory"
app_publisher = "LedgerX"
app_description = "Manufacturing as a standalone LedgerX module: production lines, barcode scanning, operator mobile screen, waste, cost and quality"
app_email = "hello@ledgerx.local"
app_license = "mit"

required_apps = ["erpnext"]

add_to_apps_screen = [
	{
		"name": "ledgerx_manufacturing",
		"logo": "/assets/ledgerx_manufacturing/images/factory.svg",
		"title": "Factory",
		"route": "/desk/factory",
		"has_permission": "ledgerx_manufacturing.install.check_app_permission",
	}
]

from ledgerx_manufacturing import __version__ as _v  # noqa: E402

app_include_js = [f"/assets/ledgerx_manufacturing/js/factory_forms.js?v={_v}"]

doc_events = {
	"Workstation": {"validate": "ledgerx_manufacturing.events.workstation_validate"},
	"Production Line": {"validate": "ledgerx_manufacturing.events.production_line_validate"},
	"Job Card": {
		"validate": "ledgerx_manufacturing.events.job_card_validate",
		"before_submit": "ledgerx_manufacturing.events.job_card_before_submit",
	},
}

after_install = "ledgerx_manufacturing.install.after_install"
after_migrate = "ledgerx_manufacturing.install.after_migrate"
