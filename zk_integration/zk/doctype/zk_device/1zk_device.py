# -*- coding: utf-8 -*-
# Copyright (c) 2021, Peter and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from zk import ZK, const
from datetime import datetime,date,timedelta , time
from frappe.utils import to_timedelta
import json
# from zk.doctype.device_log.device_log import create_employee_checkin
# from zk_integration.zk.doctype.device_log.device_log import create_employee_checkin
from frappe.utils.data import DATE_FORMAT , TIME_FORMAT 

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class ZKDevice(Document):
	@frappe.whitelist()
	def get_device_log (self):
		conn = None
		zk = ZK(self.ip, port=self.port, password=self.password,timeout=20 , force_udp=self.udp or True, ommit_ping=self.ping or True)
		# zk = ZK('192.168.1.201', port=4370, timeout=20 , ommit_ping=False)
		# if True:
		try:
			conn = zk.connect()
			# conn.disable_device()
			logs = conn.get_attendance() or []
			
			last_log_users = {}
			period = self.period or 0
			count = 1
			last = self.last_log_row
			total = len(logs)
			if self.last_log_row:
				self.last_log_row = datetime.strptime(str(self.last_log_row),DATETIME_FORMAT)
			for log in logs:
				frappe.publish_progress(count * 100 / total, title=_("Getting Logs..."))
				count += 1
				if self.last_log_row and (log.timestamp < self.last_log_row):
					continue
				last_timestamp = last_log_users.get(log.user_id) or None
				if period and last_timestamp:
					diff = (log.timestamp -  last_timestamp).seconds / 3600
					if diff < period :
						continue

				try:
				# if True:
				# frappe.msgprint(str(log))
					log.status = 'IN' if log.status ==1 else 'OUT'

					# log.status = log.status.upper()
					name = "{}-{}-{}".format(log.user_id,log.timestamp , log.status)
					sql = """
					insert Into `tabDevice Log` 
					(name,employee,enroll_no,time,date,type,punch,creation,modified , owner , device) 
					values 
					('{}',(select name from tabEmployee where attendance_device_id = '{}' limit 1),'{}','{}','{}','{}','{}',CURRENT_TIMESTAMP(),CURRENT_TIMESTAMP() , '{}','{}')
					""".format(name,log.user_id,log.user_id,log.timestamp , log.timestamp.date()
							   ,log.status,log.punch,frappe.session.user,self.name )
					# frappe.msgprint(sql)

					frappe.db.sql(sql)
					last_log_users [log.user_id] = datetime.strptime(str(log.timestamp),DATETIME_FORMAT)
				except :
						pass
				last = log.timestamp

			self.last_log_row = last
			frappe.db.commit()
			conn.test_voice()
			conn.enable_device()

		except Exception as e:
			frappe.msgprint(_("Process terminate : {}".format(e)),indicator='red')
			self.last_connection_error  = str(e)
		finally:
			self.last_connection_time = datetime.now()
			if conn:
				conn.enable_device()

				conn.disconnect()
		self.get_after_mins = self.get_after_mins or 5
		self.excecution_time = datetime.now() + timedelta(minutes=self.get_after_mins)

		self.save()
		sync_employee()
@frappe.whitelist()
def sync_employee():
	frappe.db.sql("""
	Update `tabDevice Log` log set log.employee = (
	select name from tabEmployee where attendance_device_id = log.enroll_no limit 1
	)
	""")
	frappe.db.commit()
	frappe.msgprint(_("Done"))
@frappe.whitelist()
def get_active_device_logs(names = None):
	if names :
		names = json.loads(str(names))
	devices = names or  frappe.db.sql (""" 
		select name from `tabZK Device` where docstatus < 2 and auto_attendance = 1
    and (current_timestamp() >= excecution_time or ifnull(excecution_time,0)=0) ;
	""")

	for device in devices:
		doc = frappe.get_doc("ZK Device",device)
		try:
			doc.get_device_log()
		except Exception as e:
			frappe.msgprint(_("Process terminate : {}".format(e)), indicator='red')









