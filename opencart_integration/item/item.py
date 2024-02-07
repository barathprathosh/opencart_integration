import frappe
import date
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
def fetch_oc_items():
    if opencart_settings.get("enable") == 1:
        oc = OpenCart_Items()
        oc.call()

class OpenCart_Items:
    def _init_(self):
        self.items = []

    def call(self):
        try:
            self.page = 1
            value = True
            while (value):
                self.get_items()
                if self.items:
                    for self.item in self.items:
                        if self.item_exist() and self.item.get("product_type") != 2:
                            self.create_item()
                else:
                    value = False
                self.page += 1
        except Exception as err:
            make_opencart_log(status="Error", exception=str(err))
    
    def get_items(self):
        url = "{}/api/api.php"
        headers = {
            'signature': opencart_settings.signature,
            'token': opencart_settings.api_token,
            'Cookie': 'currency=INR; language=en-gb; currency=INR; language=en-gb'
        }
        params = {
            "rquest":"getproducts",
            "language_id":1,
            "page":self.page
        }
        response = requests.get(url.format(opencart_settings.api_url), params=params, headers=headers)
        response = response.json()
        if response.get("status") == "200":
            self.items = response.get("products")
        else:
            raise make_opencart_log(status="Error", exception=str(response))
        return
    
    def item_exist(self):
        item_code = frappe.get_value("Item",{"name":self.item.get("model")},["name"])
        item_exists = True
        if item_code:            
            item_exists = False
        return item_exists
    
    def create_item(self):
        product_category = self.get_product_category()
        discount_items = self.get_discount_items()
        special_discount = self.get_special_discount_items()
        disable = quantity = 0
        if float(self.item.get("quantity")) > 0:
            quantity = float(self.item.get("quantity"))
        else:
            quantity = 1
        if self.item.get("status") == 0:
            disable = 1
        try:
            item_doc = frappe.get_doc({
                "doctype": "Item",
                "item_code": self.item.get("model"),
                "disable": disable,
                "is_stock_item":1,
                "opening_stock":quantity,
                "product_id": self.item.get("product_id"),
                "item_name": self.item.get("name"),
                "item_group": opencart_settings.item_group,
                "product_category":product_category,
                "is_stock_item": 1,
                "valuation_rate":float(self.item.get("upc") or 1),
                "stock_uom": opencart_settings.stock_uom,
                "standard_rate": self.item.get("price"),
                "gst_hsn_code": self.item.get("hsn"),
                "description": self.item.get("email"),
                "date_available": self.item.get("date_available"),
                "length": self.item.get("length"),
                "width": self.item.get("width"),
                "height": self.item.get("height"),
                "weight": self.item.get("weight"),
                "weight_class": self.item.get("weight_class"),
                "length_class": self.item.get("length_class"),
                "stock_status": self.item.get("stock_status"),
                "discount_items":discount_items,
                "special_discount_items":special_discount,
                "brand":self.item.get("manufacturer"),
            })
            item_doc.insert(ignore_mandatory=True)
            frappe.db.commit()
        except Exception as err:
            make_opencart_log(status="Error", exception=str(err)+" Product ID: "+str(self.item.get("product_id")))
        return

    def get_product_category(self):
        category_list = []
        for category in self.item.get("categories"):
            if category:
                product_category = frappe.get_value("Product Category",{"name":category.get("name")},["name"])
                if product_category:
                    category_list.append({"product_category":product_category})
                else:
                    try:
                        product_category = frappe.get_doc({
                            "doctype":"Product Category",
                            "category_name":category.get("name")
                        })
                        product_category.insert(ignore_mandatory=True)
                        frappe.db.commit()
                        category_list.append({"product_category":product_category.name})
                    except Exception as err:
                        make_opencart_log(status="Error", exception=str(err)+str( "Product ID: ",self.item.get("product_id")))
        return category_list

    def get_discount_items(self):
        discount_items = []
        for item in self.item.get("product_discounts_all"):
            if item:
                item_group = "Dealer" if item.get("customer_group_id") == "2" else "end user"
                discount_items.append({
                    "customer_group": item_group,
                    "start_date": item.get("date_start"),
                    "end_date": item.get("date_end"),
                    "qty":item.get("quantity"),
                    "priority":item.get("priority"),
                    "price":float(item.get("price").strip("₹").replace("₹",""))
                })
        return discount_items
    
    def get_special_discount_items(self):
        special_discount_items = []
        for item in self.item.get("product_special_all"):
            if item:
                item_group = "Dealer" if item.get("customer_group_id") == "2" else "end user"
                special_discount_items.append({
                    "customer_group": item_group,
                    "start_date": item.get("date_start"),
                    "end_date": item.get("date_end"),
                    "priority":item.get("priority"),
                    "price":float(item.get("price").strip("₹").replace("₹",""))
                })
        return special_discount_items
