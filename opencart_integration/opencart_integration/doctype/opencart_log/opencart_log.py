# Copyright (c) 2022, Barath Prathosh and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder import Interval
from frappe.query_builder.functions import Now


class OpencartLog(Document):
	def onload(self):
		if not self.seen and not frappe.flags.read_only:
			self.db_set("seen", 1, update_modified=0)
			frappe.db.commit()

	@staticmethod
	def clear_old_logs(days=30):
		table = frappe.qb.DocType("Opencart Log")
		frappe.db.delete(table, filters=(table.modified < (Now() - Interval(days=days))))


@frappe.whitelist()
def clear_error_logs():
	"""Flush all Error Logs"""
	frappe.only_for("System Manager")
	frappe.db.truncate("Opencart Log")

def make_opencart_log(status="Queued", exception=None, rollback=False):
	# if name not provided by log calling method then fetch existing queued state log

	if rollback:
		frappe.db.rollback()

	log = frappe.get_doc({"doctype":"Opencart Log"}).insert(ignore_permissions=True)

	log.method = get_message(exception)
	log.traceback = frappe.get_traceback()
	log.status = status
	log.save(ignore_permissions=True)
	frappe.db.commit()

def get_message(exception):
	message = None

	if hasattr(exception, 'message'):
		message = exception.get("message")
	elif hasattr(exception, '__str__'):
		message = exception.__str__()
	else:
		message = "Something went wrong"
	return message