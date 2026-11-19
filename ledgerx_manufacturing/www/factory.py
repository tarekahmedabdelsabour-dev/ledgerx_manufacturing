import frappe

no_cache = 1
sitemap = 0


def get_context(context):
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login?redirect-to=/factory"
		raise frappe.Redirect
	context.no_cache = 1
	context.show_sidebar = False
	context.title = frappe._("Operator Screen")
	context.csrf_token = frappe.sessions.get_csrf_token()
	context.lang_code = (frappe.local.lang or "en")[:2]
	context.beep = 1 if frappe.db.get_single_value("Factory Settings", "scan_sound") else 0
