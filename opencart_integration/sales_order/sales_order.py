import frappe
from frappe.utils.data import today
import requests
from opencart_integration.opencart_integration.doctype.opencart_log.opencart_log import make_opencart_log
import json
from datetime import datetime, timedelta
from erpnext import get_default_company
from frappe import _
from frappe.utils import (
	add_days,
	add_months,
	cint,
	date_diff,
	flt,
	get_first_day,
	get_last_day,
	get_link_to_form,
	getdate,
	rounded,
	today,
)

opencart_settings = frappe.get_doc("Opencart Settings")

@frappe.whitelist()
def fetch_oc_orders():
    if opencart_settings.get("enable") == 1:
        oc = OpenCart()
        oc.call()

class OpenCart:
    def _init_(self):
        self.orders = []

    def call(self):
        try:
            self.get_orders()
            # for self.order in self.orders:
            #     if not self.order_exits():
            #         self.customer_fname = ''
            #         self.customer_lname = ''
            #         self.items_arr = []
            #         self.address = ''
            #         self.items_in_sys = []
            #         self.taxes = []  # Applies to items and shipment also
            #         self.is_guest = False
            #         self.get_customer()
            #         self.get_address()
            #         self.get_items()
            #         self.get_taxes()
            #         self.get_shipment_taxes()
            #         self.create_shipping_rule()
            #         self.create_so()
            #     else:
            #         print("Order exits")
        except Exception as err:
            make_opencart_log(status="Error", exception=str(err))
    
    def get_orders(self):
        url = "{}/api/invoiceapi.php"
        from_date = add_days(today(), -1)
        headers = {
            'signature': opencart_settings.signature,
            'token': opencart_settings.api_token,
            'Cookie': 'currency=INR; language=en-gb; currency=INR; language=en-gb'
        }
        params = {
            "rquest":"getorderslist",
            "page":1,
            "start_date":from_date,
            "start_time":"12:32:00",
            "end_date":today(),
            "end_time":"23:59:59",
        }
        response = requests.get(url.format(opencart_settings.api_url), params=params, headers=headers)
        response = response.json()
        print(response)
        if response.get("status") == 200:
            self.orders = response.get("products")
            print(response)
        else:
            make_opencart_log(status="Error", exception=str(response))