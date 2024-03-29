from . import __version__ as app_version

app_name = "opencart_integration"
app_title = "Opencart Integration"
app_publisher = "Barath Prathosh"
app_description = "Opencart Integration with ERPNext"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "barathprathosh@gmail.com"
app_license = "MIT"

# Includes in <head>
# ------------------

fixtures = ["Property Setter","Custom Field"]

# include js, css files in header of desk.html
# app_include_css = "/assets/opencart_integration/css/opencart_integration.css"
# app_include_js = "/assets/opencart_integration/js/opencart_integration.js"

# include js, css files in header of web template
# web_include_css = "/assets/opencart_integration/css/opencart_integration.css"
# web_include_js = "/assets/opencart_integration/js/opencart_integration.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "opencart_integration/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "opencart_integration.install.before_install"
# after_install = "opencart_integration.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "opencart_integration.uninstall.before_uninstall"
# after_uninstall = "opencart_integration.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "opencart_integration.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
    "Purchase Receipt":{
        "on_submit":"opencart_integration.purchase_receipt.purchase_receipt.update_stock_oc",
        "on_cancel":"opencart_integration.purchase_receipt.purchase_receipt.update_stock_oc",
        "validate":"opencart_integration.purchase_receipt.purchase_receipt.get_stock_balance_qty"
    }
}

# Scheduled Tasks
# ---------------

scheduler_events = {
#	"all": [
#		"opencart_integration.tasks.all"
#	],
    "cron": {
		"*/10 * * * *":[
			"opencart_integration.sales_order.sales_order.fetch_oc_orders"
		],
    },
	"daily": [
        "opencart_integration.item.item.fetch_oc_items",
        "opencart_integration.customer.customer.fetch_oc_customers",
        "opencart_integration.deleted_document.deleted_document.clear_deleted_document"
		# "opencart_integration.tasks.daily"
	],
#	"hourly": [
#		"opencart_integration.tasks.hourly"
#	],
#	"weekly": [
#		"opencart_integration.tasks.weekly"
#	]
#	"monthly": [
#		"opencart_integration.tasks.monthly"
#	]
}

# Testing
# -------

# before_tests = "opencart_integration.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "opencart_integration.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "opencart_integration.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
    {
        "doctype": "{doctype_1}",
        "filter_by": "{filter_by}",
        "redact_fields": ["{field_1}", "{field_2}"],
        "partial": 1,
    },
    {
        "doctype": "{doctype_2}",
        "filter_by": "{filter_by}",
        "partial": 1,
    },
    {
        "doctype": "{doctype_3}",
        "strict": False,
    },
    {
        "doctype": "{doctype_4}"
    }
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"opencart_integration.auth.validate"
# ]

