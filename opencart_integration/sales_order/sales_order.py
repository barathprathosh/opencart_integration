import frappe
from frappe.utils.data import today
import requests
from opencart_integration.opencart_integration.doctype.opencart_log.opencart_log import make_opencart_log
import json
from datetime import datetime, timedelta
from erpnext import get_default_company
from frappe import _
from frappe.utils import (add_days,nowdate,add_months,cint,date_diff,flt,get_first_day,get_last_day,get_link_to_form,getdate,rounded,today)
from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

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
            self.page = 1
            value = True
            while (value):
                self.get_orders()
                if self.orders:
                    for self.order in self.orders:
                        if self.order.get("order_status") in ["Processed","Shipped","Complete","Ready to ship"]:
                            if not self.order_exits():
                                self.customer_fname = ""
                                self.customer_lname = ""
                                self.shipping_address_name = ""
                                self.payment_address_name = ""
                                self.items_arr = []
                                self.sales_channel = ""
                                self.source_warehouse = ""
                                self.delivery_warehouse = ""
                                self.items_in_sys = []
                                self.taxes = []
                                self.discount = 0.0  # Applies to items and shipment also
                                self.is_guest = False
                                self.get_sales_channel()
                                self.get_customer()
                                self.get_address()
                                self.get_items()
                                self.get_taxes_discount()
                                self.sales_order = self.create_so()
                                self.sales_invoice = self.create_si()
                                self.create_pe()
                            else:
                                print("Order exits")
                        elif self.order.get("order_status") in ["Failed","Canceled"]:
                            if self.order_exits():
                                self.failed_order()
                else:
                    value = False
                self.page += 1
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
            "page":self.page,
            "start_date":from_date,
            "start_time":"00:00:01",
            "end_date":today(),
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
            so = frappe.db.get_value("Sales Order", {"po_no": self.order.get("order_id"), "sales_channel": sales_channel,"docstatus":1}, "name")
            order_exists = False
            if so:
                order_exists = True
            return order_exists
    
    def get_sales_channel(self):
        sales_details = frappe.get_list("Sales Channel",{"store_id":self.order.get("store_id")},["name","source_warehouse","delivery_warehouse"])
        if sales_details:
            self.sales_channel = sales_details[0].name
            self.source_warehouse = sales_details[0].source_warehouse
            self.delivery_warehouse = sales_details[0].delivery_warehouse
        return
    
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
                "customer_group": self.order.get("customer_group_name")
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
        return
    
    def shipping_address(self,shipping_name):
        address = frappe.get_value("Address",
        {
            "address_type":"Shipping",
            "customer_id": self.order.get("customer_id"),
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
                    "customer_id": self.order.get("customer_id"),
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
            "customer_id": self.order.get("customer_id"),
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
                    "customer_id": self.order.get("customer_id"),
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
        items_array = []
        increment_id = 0
        for order_item in self.order.get("products"):
            item = frappe.db.get_value("Item", {"item_code": order_item["model"],"disabled":0}, "name")
            if item is None:
                mail_msg = " In Opencart Order " + str(increment_id) + " following are Invalid Line Item " + str(order_item["model"])
                make_opencart_log(status="Error", exception=mail_msg)
            else:
                items_array.append({
                    "item_code": str(order_item.get("model")),
                    "item_name": order_item.get("name"),
                    "rate": float(order_item.get("price").strip("₹").replace("₹","")),
                    "delivery_date": self.order.get("date_modified").split(" ")[0],
                    "qty": order_item.get("quantity"),
                    "warehouse": self.delivery_warehouse
                })
            increment_id+=1
        for tax in self.order.get("order_totals"):
            if tax:
                if tax.get("code") == "advancedpostcodecod":
                    if float(tax.get("value")) > 0:
                        items_array.append({
                            "item_code": "Cash on Delivery Fee",
                            "item_name": "Cash on Delivery Fee",
                            "rate": float(tax.get("value")),
                            "delivery_date": self.order.get("date_modified").split(" ")[0],
                            "qty": 1,
                            "warehouse": self.delivery_warehouse
                        })
                if tax.get("code") == "shipping":
                    if float(tax.get("value")) > 0:
                        items_array.append({
                            "item_code": "Shipping Charges",
                            "item_name": "Shipping Charges",
                            "rate": float(tax.get("value")),
                            "delivery_date": self.order.get("date_modified").split(" ")[0],
                            "qty": 1,
                            "warehouse": self.delivery_warehouse
                        })
        self.items_in_sys = items_array
        return
        
    def get_taxes_discount(self):
        tax_array = []
        discount = 0
        tax_array.append({
            "charge_type":"On Net Total",
            "account_head":"CGST-9% - GCIL",
            "description":"CGST-9% - GCIL",
            "cost_center":"Main - GCIL",
            "rate":9,
            "included_in_print_rate":1
        })
        tax_array.append({
            "charge_type":"On Net Total",
            "account_head":"SGST-9% - GCIL",
            "description":"SGST-9% - GCIL",
            "cost_center":"Main - GCIL",
            "rate":9,
            "included_in_print_rate":1
        })
        for tax in self.order.get("order_totals"):
            if tax:
                if tax.get("code") == "coupon":
                    if tax.get("value"):
                        discount += float(tax.get("value"))
                if tax.get("code") == "reward":
                    if tax.get("value"):
                        discount += float(tax.get("value"))
                if tax.get("code") == "tax":
                    if tax.get("value"):
                        tax_array.append({
                            "charge_type":"Actual",
                            "account_head":opencart_settings.tax_account,
                            "description":"Taxes",
                            "cost_center":opencart_settings.cost_center,
                            "tax_amount":tax.get("value")
                        })
        self.taxes = tax_array
        self.discount = discount
        return

    def create_so(self):
        try:
            frappe.set_user('Administrator')
            purchase_date = self.order.get("date_added").split(" ")[0]
            delivery_date = self.order.get("date_modified").split(" ")[0]
            so = frappe.get_doc({
                "doctype": "Sales Order",
                "order_type":"Sales",
                "transaction_date":purchase_date,
                "set_warehouse": self.source_warehouse,
                "po_no": self.order.get("order_id"),
                "po_date": purchase_date,
                "customer": self.customer,
                "sales_channel":self.sales_channel,
                "delivery_date": delivery_date,
                "ignore_pricing_rule": 1,
                "items": self.items_in_sys,
                "company": frappe.db.get_single_value("Global Defaults", "default_company"),
                "taxes": self.taxes,
                "customer_address": self.payment_address_name,
                "shipping_address_name": self.shipping_address_name,
                "apply_discount_no":"Grand Total",
                "discount_amount":self.discount
            })
            so.flags.ignore_mandatory = True
            so.save(ignore_permissions=True)
            so.submit()
            make_opencart_log(status="Success", exception="New sale order " + so.name + " created successfully")
            return so
        except Exception as err:
            make_opencart_log(status="Error", exception="Sale order creation err-" + str(err))
    
    def create_si(self):
        if self.sales_order:
            try:
                sales_invoice = make_sales_invoice(self.sales_order.name, ignore_permissions=True)
                sales_invoice.set_posting_time = 1
                sales_invoice.update_stock = 1
                sales_invoice.posting_date = self.order.get("date_added").split(" ")[0]
                sales_invoice.due_date = self.order.get("date_modified").split(" ")[0]
                sales_invoice.flags.ignore_mandatory = True
                sales_invoice.insert(ignore_mandatory=True)
                sales_invoice.submit()
                frappe.db.commit()
                make_opencart_log(status="Success", exception="New Sales Invoice " + sales_invoice.name + " created successfully")
                return sales_invoice
            except Exception as err:
                make_opencart_log(status="Error", exception="Sale Invoice creation err-" + str(err))
                cancel_order(array = [{
                            "doctype":"Sales Order",
                            "name":self.sales_order
                        }])

        
    def create_pe(self):
        if self.sales_invoice:
            try:
                payment_method,account = self.get_payment_method()
                payment_entry = get_payment_entry("Sales Invoice", self.sales_invoice.name)
                payment_entry.reference_no = self.sales_invoice.name
                payment_entry.mode_of_payment = payment_method
                payment_entry.paid_to = account
                payment_entry.paid_amount = float(self.order.get("total").strip("₹").replace("₹",""))
                payment_entry.reference_date = nowdate()
                payment_entry.custom_remarks = 1
                payment_entry.remarks = self.order.get("payment_method")
                payment_entry.flags.ignore_mandatory = True
                payment_entry.insert(ignore_permissions=True)
                payment_entry.submit()
                make_opencart_log(status="Success", exception="New payment entry " + payment_entry.name + " created successfully")
            except Exception as err:
                make_opencart_log(status="Error", exception="Payment Entry creation err-" + str(err))
    
    def get_payment_method(self):
        if self.order.get("payment_code") == "cod":
            return "Cash","1110 - Cash - GCIL"
        elif self.order.get("payment_code") == "razorpay":
            return "Wire Transfer","Razorpay - GCIL"
        if self.order.get("payment_code") == "paytm":
            return "Wire Transfer","Paytm - GCIL"
        else:
            return "Wire Transfer","IDBI Bank - GCIL"
        
    def failed_order(self):
        array = []
        sales_channel = frappe.get_value("Sales Channel",{"store_id":self.order.get("store_id")},["name"])
        if sales_channel:            
            sales_order = frappe.db.get_value("Sales Order", {"po_no": self.order.get("order_id"), "sales_channel": sales_channel,"docstatus":1}, "name")
            if sales_order:
                array.insert(0,{
                    "doctype":"Sales Order",
                    "name":sales_order
                })
                sales_invoice = frappe.get_value("Sales Invoice Item",{"docstatus":1,"sales_order":sales_order},"parent")
                if sales_invoice:
                    array.insert(0,{
                        "doctype":"Sales Invoice",
                        "name":sales_invoice
                    })
                    payment_entry = frappe.get_value("Payment Entry Reference",{"docstatus":1,"reference_doctype":"Sales Invoice","reference_name":sales_invoice},"parent")
                    if payment_entry:
                        array.insert(0,{
                            "doctype":"Payment Entry",
                            "name":payment_entry
                        })
                        cancel_order(array)
                    else:
                        cancel_order(array)
                else:
                    cancel_order(array)
        return

def cancel_order(array):
    for order in array:
        try:
            doc = frappe.get_doc(order.get("doctype"),order.get("name"))
            doc.cancel()
            frappe.db.commit()
        except Exception as err:
                make_opencart_log(status="Error", exception="Doctype Cancel error-" + str(err))
    return
