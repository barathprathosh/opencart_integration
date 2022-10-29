# Copyright (c) 2022, Barath Prathosh and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class OpencartSettings(Document):
	pass

import requests

@frappe.whitelist()
def get_api_token():
	url = "https://dev.sparesale.com/index.php?route=api/login"

	payload={'username': 'opencart_erp',
	'key': 'tgvrO4RwCxcMtBWhLNRcr1Y1pk4WzlKyASqukNta6tSThsQFnScoJAHknARVGvZzuGp8rs2Ou30bAEXLQJvjcvhXb3PP57nlJIzoA22n8syHQMBsTs0ubFAxo8gWK7PNsCbNZbtbjLEav26dZ1AFRy3A4kKY0NPzQqOzJPRPxroNW7xT26NJrcyvkROIg1niWiOFyQX65VVIK7jgyKFXzI4rviLaH7Gla8UInl4ueqGVIMNMmBxIbWnSefrXaAKs'}
	files=[

	]
	headers = {
	'Cookie': 'currency=INR; language=en-gb; OCSESSID=33513d7123cbaf9931b27dc6ac; currency=INR; language=en-gb'
	}

	response = requests.request("POST", url, headers=headers, data=payload, files=files)

	frappe.errprint(response.text)