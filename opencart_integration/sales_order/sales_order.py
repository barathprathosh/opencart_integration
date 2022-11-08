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
            for self.order in self.orders:
                if not self.order_exits():
                    self.customer_fname = ""
                    self.customer_lname = ""
                    self.shipping_address_name = ""
                    self.payment_address_name = ""
                    self.items_arr = []
                    self.address = ''
                    self.items_in_sys = []
                    self.taxes = []  # Applies to items and shipment also
                    self.is_guest = False
                    self.get_customer()
                    self.get_address()
                    self.get_items()
                    self.get_taxes()
                    self.get_shipment_taxes()
                    self.create_shipping_rule()
                    self.create_so()
                else:
                    print("Order exits")
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
            "start_date":"2020-08-21",
            "start_time":"12:32:00",
            "end_date":"2020-08-21",
            "end_time":"23:59:59",
        }
        response = requests.get(url.format(opencart_settings.api_url), params=params, headers=headers)
        response = response.json()
        if response.get("status") == 200:
            self.orders = response.get("orders")
        else:
            make_opencart_log(status="Error", exception=str(response))
        return
    
    def order_exits(self):
        sales_channel = frappe.get_value("Sales Channel",{"store_id":self.order.get("store_id")},["name"])
        if sales_channel:
            so = frappe.db.get_value("Sales Order", {"order_id": self.order.get("order_id"), "up_sales_channel": sales_channel}, "name")
            order_exists = False
            if so:
                order_exists = True
            return order_exists
    
    def get_customer(self):
        self.customer_fname = self.order.get("firstname")
        self.customer_lname = self.order.get("lastname")

        customer_name = frappe.db.get_value("Customer", {"customer_id": self.order.get('customer_id')},"name")

        if not customer_name:
            self.create_customer()
            self.get_customer()
        else:
            self.customer = customer_name
        return
    
    def create_customer(self):
        try:
            customer_entry = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": self.customer_fname + " " + self.customer_lname,
                "customer_id": self.order.get('customer_id'),
                "territory": frappe.utils.nestedset.get_root_of("Territory"),
                "customer_type": opencart_settings.customer_type,
                "customer_group": opencart_settings.customer_group
            })
            customer_entry.flags.ignore_mandatory = True
            customer_entry.insert(ignore_permissions=True)
            frappe.db.commit()
        except Exception as err:
            make_opencart_log(status="Error", exception="Error while creating new customer" + str(err))

    def get_address(self):
        shipping_name = self.order.get("shipping_firstname") +" "+self.order.get("shipping_lastname")
        payment_name = self.order.get("payment_firstname") +" "+self.order.get("payment_lastname")
        self.shipping_address_name = self.shipping_address(shipping_name)
        self.payment_address_name = self.payment_address(payment_name)
        # self.shipping_address = self.save_address(shipping_details)
        # self.payment_address = self.save_address(payment_details)
    
    def shipping_address(self,shipping_name):
        address = frappe.get_value("Address",
        {
            "address_type":"Shipping",
            "link_name": self.customer,
            "address_line1":self.order.get("shipping_address_1"),
            "address_line2":self.order.get("shipping_address_2"),
            "city":self.order.get("shipping_city"),
            "state":self.order.get("shipping_zone"),
            "country":self.order.get("shipping_country"),
            "pincode":self.order.get("shipping_postcode")
            },["name"])
        if not address:
            try:
                frappe.set_user('Administrator')
                doc = frappe.get_doc({
                    "doctype": "Address",
                    "address_title": shipping_name,
                    "address_type": "Shipping",
                    "address_line1": self.order.get("shipping_address_1"),
                    "address_line2": self.order.get("shipping_address_2"),
                    "city": self.order.get("shipping_city"),
                    "state": self.order.get("shipping_zone"),
                    "pincode": self.order.get("shipping_postcode"),
                    "country": self.order.get("shipping_country"),
                    "phone": self.order.get("telephone"),
                    "email_id": self.order.get("email"),
                    "links": [{
                        "link_doctype": "Customer",
                        "link_name":  self.customer
                    }]
                })
                doc.insert(ignore_mandatory=True)
                frappe.db.commit()
                return doc.name
            except Exception as err:
                make_opencart_log(status="Error", exception="Error while creating Shipping Address" + str(err))
        else:
            shipping_details = address
        return shipping_details
    
    def payment_address(self,payment_name):
        address = frappe.get_value("Address",
        {
            "address_type":"Billing",
            "link_name": self.customer,
            "address_line1":self.order.get("payment_address_1"),
            "address_line2":self.order.get("payment_address_2"),
            "city":self.order.get("payment_city"),
            "state":self.order.get("payment_zone"),
            "country":self.order.get("payment_country"),
            "pincode":self.order.get("payment_postcode")
            },["name"])
        if not address:
            try:
                frappe.set_user('Administrator')
                doc = frappe.get_doc({
                    "doctype": "Address",
                    "address_title": payment_name,
                    "address_type": "Billing",
                    "address_line1": self.order.get("payment_address_1"),
                    "address_line2": self.order.get("payment_address_2"),
                    "city": self.order.get("payment_city"),
                    "state": self.order.get("payment_zone"),
                    "pincode": self.order.get("payment_postcode"),
                    "country": self.order.get("payment_country"),
                    "phone": self.order.get("telephone"),
                    "email_id": self.order.get("email"),
                    "links": [{
                        "link_doctype": "Customer",
                        "link_name":  self.customer
                    }]
                })
                doc.insert(ignore_mandatory=True)
                frappe.db.commit()
                return doc.name
            except Exception as err:
                make_opencart_log(status="Error", exception="Error while creating Billing Address" + str(err))
        else:
            payment_details = address
        return payment_details
    
    def get_items(self):

        order_items = self.order.get("products")
        items_array = []
        increment_id = 0
        for order_item in order_items:
            model = order_item["model"]
            item = frappe.db.get_value("Item", {"item_code": model}, "name")
            if item is None:
                mail_msg = " In Opencart Order " + str(increment_id) + " following are Invalid Line Item " + str(model)
                make_opencart_log(status="Error", exception=mail_msg)
            else:
                price = flt(order_item.get("price"))
                discount = flt(order_item.get("discount_amount")/order_item.get("qty_ordered"))
                induvidual_rate = price - discount
                delivery_date = self.order["updated_at"].split(" ")[0]
                items_array.append({
                    "item_code": str(order_item.get("model")),
                    "item_name": order_item.get("name"),
                    "rate": induvidual_rate,
                    # Note: This method to be added
                    "delivery_date": self.get_date_warehouse_lt(delivery_date),
                    "qty": order_item.get("quantity"),
                    "warehouse": self.get_item_level_warehouse(),  # Note: This method to be added
                })
            increment_id+=1
        self.items_in_sys = items_array