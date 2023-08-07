# -*- coding: utf-8 -*-
# Copyright (c) 2021, Peter and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from zk_integration.zk.doctype.zk_device.zk_device import sync_employee
from zk_integration.zk.doctype.zk_device.zk_device import get_active_device_logs

class DeviceLog(Document):
	pass
@frappe.whitelist()
def create_employee_checkin(names=None):
	sync_employee()
	sql = """
	Insert Into `tabEmployee Checkin` (name , employee , time , log_type,device_log,device,creation,modified,owner)
	(select name , employee , time , type,name,device,creation,modified,owner from `tabDevice Log` where employee is not null
	and  name not in (select device_log from `tabEmployee Checkin` where device_log is not null));
	"""
	# frappe.msgprint(sql)
	frappe.db.sql(sql)
	frappe.db.commit()

def execute (names=None):
	try:
		get_active_device_logs()
	except :
		pass
	try:
		sync_employee()
	except :
		pass
	try:
		create_employee_checkin()
	except :
		pass
