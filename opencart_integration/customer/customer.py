import frappe
import requests
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
def fetch_oc_customers():
    if opencart_settings.get("enable") == 1:
        oc = OpenCart_Customers()
        oc.call()

class OpenCart_Customers:
    def _init_(self):
        self.customers = []

    def call(self):
        try:
            self.page = 1
            value = True
            while (value):
                self.get_customers()
                if self.customers:
                    for self.customer in self.customers:
                        if self.customer_exist():
                            customer_name = self.create_customer()
                            self.create_address(customer_name)
                            return
                else:
                    value = False
                self.page += 1
        except Exception as err:
            make_opencart_log(status="Error", exception=str(err))
    
    def get_customers(self):
        url = "{}/api/api.php"
        headers = {
            'signature': opencart_settings.signature,
            'token': opencart_settings.api_token,
            'Cookie': 'currency=INR; language=en-gb; currency=INR; language=en-gb'
        }
        params = {
            "rquest":"get_customers",
            "page":self.page,
            "with_address":1          
        }
        response = requests.get(url.format(opencart_settings.api_url), params=params, headers=headers)
        response = response.json()
        if response.get("status") == "200":
            self.customers = response.get("data")
        else:
            make_opencart_log(status="Error", exception=str(response))
        return
    
    def customer_exist(self):
        customer_name = frappe.db.get_value("Customer", {"customer_id": self.customer.get('customer_id')},"name")
        customer_exists = True
        if customer_name:            
            customer_exists = False
        return customer_exists
    
    def create_customer(self):
        try:
            customer_entry = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": self.customer.get('firstname') + " " + self.customer.get('lastname'),
                "customer_id": self.customer.get('customer_id'),
                "territory": frappe.utils.nestedset.get_root_of("Territory"),
                "customer_type": opencart_settings.customer_type,
                "customer_group": self.customer.get('customer_group')
            })
            customer_entry.flags.ignore_mandatory = True
            customer_entry.insert(ignore_permissions=True)
            frappe.db.commit()
            return customer_entry.name
        except Exception as err:
            make_opencart_log(status="Error", exception="Error while creating new customer" + str(err))

    def create_address(self,customer_name):
        if self.customer.get('address'):
            for address in self.customer.get('address'):
                address_doc = frappe.get_value("Address",{"address_id":address.get('address_id'),"customer_id":self.customer.get('customer_id'),"link_name": customer_name},["name"])
                if not address_doc:
                    if self.customer.get('address_id') == address.get('address_id'):
                        self.payment_address(address,customer_name)
                        return
                    else:
                        self.shipping_address(address,customer_name)
                        print(address)
                        return
        return
    
    def shipping_address(self,address,customer_name):
        try:
            frappe.set_user('Administrator')
            doc = frappe.get_doc({
                "doctype": "Address",
                "address_title": address,
                "address_type": "Shipping",
                "address_line1": self.customer.get("shipping_address_1"),
                "address_line2": self.customer.get("shipping_address_2"),
                "city": self.customer.get("shipping_city"),
                "state": self.customer.get("shipping_zone"),
                "pincode": self.customer.get("shipping_postcode"),
                "country": self.customer.get("shipping_country"),
                "phone": self.customer.get("telephone"),
                "email_id": self.customer.get("email"),
                "links": [{
                    "link_doctype": "Customer",
                    "link_name":  customer_name
                }]
            })
            doc.insert(ignore_mandatory=True)
            frappe.db.commit()
            return doc.name
        except Exception as err:
            make_opencart_log(status="Error", exception="Error while creating Shipping Address" + str(err))
    
    def payment_address(self,address,customer_name):
        try:
            frappe.set_user('Administrator')
            doc = frappe.get_doc({
                "doctype": "Address",
                "address_title": address,
                "address_type": "Billing",
                "address_line1": self.customer.get("payment_address_1"),
                "address_line2": self.customer.get("payment_address_2"),
                "city": self.customer.get("payment_city"),
                "state": self.customer.get("payment_zone"),
                "pincode": self.customer.get("payment_postcode"),
                "country": self.customer.get("payment_country"),
                "phone": self.customer.get("telephone"),
                "email_id": self.customer.get("email"),
                "links": [{
                    "link_doctype": "Customer",
                    "link_name":  customer_name
                }]
            })
            doc.insert(ignore_mandatory=True)
            frappe.db.commit()
            return doc.name
        except Exception as err:
            make_opencart_log(status="Error", exception="Error while creating Billing Address" + str(err))