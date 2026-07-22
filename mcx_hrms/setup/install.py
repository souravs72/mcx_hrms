# Copyright (c) 2026, Ascra Technologies LLP and contributors
# For license information, please see license.txt

"""Production-safe idempotent setup for MCX HRMS."""

from __future__ import annotations

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from mcx_hrms.setup.demo import setup_demo_site
from mcx_hrms.setup.settings import ensure_singleton_settings
from mcx_hrms.setup.workflows import ensure_workflows


def ensure_custom_fields():
	"""Ensure LMS link fields exist on Training Event."""
	create_custom_fields(
		{
			"Training Event": [
				{
					"fieldname": "lms_course",
					"label": "LMS Course",
					"fieldtype": "Link",
					"options": "LMS Course",
					"insert_after": "course",
					"in_standard_filter": 1,
					"description": "Linked LMS course for online training content",
				},
				{
					"fieldname": "lms_batch",
					"label": "LMS Batch",
					"fieldtype": "Link",
					"options": "LMS Batch",
					"insert_after": "lms_course",
					"depends_on": "eval:doc.lms_course",
					"allow_on_submit": 1,
					"in_standard_filter": 1,
					"description": "Linked LMS batch for attendee enrollment",
				},
			]
		},
		ignore_validate=True,
	)


def setup():
	"""Apply MCX HRMS configuration (idempotent)."""
	if "hrms" not in frappe.get_installed_apps():
		return

	ensure_custom_fields()
	ensure_workflows()
	ensure_singleton_settings()
	frappe.db.commit()
	frappe.clear_cache()


def after_install():
	setup()
	setup_demo_site()
	frappe.db.commit()
	frappe.clear_cache()
