import frappe
from frappe.utils.data import today
from frappe.utils import (add_days,nowdate,add_months,cint,date_diff,flt,get_first_day,get_last_day,get_link_to_form,getdate,rounded,today)

@frappe.whitelist()
def clear_deleted_document():
    from_date = add_days(today(), -15)
    deleted_document = frappe.db.sql("""SELECT name FROM `tabDeleted Document` WHERE creation < %s """,from_date,as_dict=True)
    for dd in deleted_document:
        print(dd)
        doc = frappe.get_doc("Deleted Document",dd.name)
        doc.delete()
        frappe.db.commit()
    return