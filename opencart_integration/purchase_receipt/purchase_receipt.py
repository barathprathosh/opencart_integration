import frappe
from frappe.utils.data import today
import requests
from opencart_integration.opencart_integration.doctype.opencart_log.opencart_log import make_opencart_log
import json
from datetime import datetime, timedelta
from erpnext import get_default_company
from erpnext.stock.utils import get_stock_balance
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
def get_stock_balance_qty(self,status):
    for item in self.items:
        stock_balance = get_stock_balance(item.item_code,item.warehouse)
        if stock_balance:
            item.stock_balance_quantity = stock_balance
    return
def update_stock_oc(self,status):
    if opencart_settings.get("enable") == 1:
        stock_data = []
        for item in self.items:
            product_id = frappe.get_value("Item",{"name":item.item_code},["product_id"])
            if status == "on_submit":
                stock_balance = float(item.received_qty) + float(item.stock_balance_quantity)
            elif status == "on_cancel":
                stock_balance = float(item.stock_balance_quantity)
            if product_id:
                stock_data.append({
                    "product_id": product_id,
                    "quantity": float(stock_balance)
                })
            else:
                frappe.throw(("Product ID Missing in Item: {0} and Row No.: {1}").format(item.item_code,item.idx))
        update_stock = update_stock_api(self,stock_data)
    return

def update_stock_api(self,stock_data):
    url = "{}/api/invoiceapi.php"
    headers = {
        'signature': opencart_settings.signature,
        'token': opencart_settings.api_token,
        'Content-Type': 'application/json'
    }
    params = {
        "rquest":"update_qty"
    }
    payload = json.dumps({
        "products":stock_data
    })
    response = requests.post(url.format(opencart_settings.api_url), params=params, headers=headers, data=payload)
    response = response.json()
    if response.get("status") == "200":
        make_opencart_log(status="Success", exception="Purchase Receipt: "+str(self.name)+" Stock Updated Successfully in OpenCart Website")
        return response
    else:
        raise make_opencart_log(status="Error", exception=str(response))
    return