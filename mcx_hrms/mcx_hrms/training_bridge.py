# Copyright (c) 2026, Ascra Technologies LLP and contributors
# For license information, please see license.txt

"""LMS ↔ HRMS Training Event bridge."""

from __future__ import annotations

import frappe
from frappe import _

LMS_INSTALLED = lambda: "lms" in frappe.get_installed_apps()


def _require_lms():
	if not LMS_INSTALLED():
		frappe.throw(_("LMS app is not installed on this site"))


def _get_event(training_event: str):
	frappe.has_permission("Training Event", "read", training_event, throw=True)
	return frappe.get_doc("Training Event", training_event)


def _employee_user(employee: str) -> str | None:
	return frappe.db.get_value("Employee", employee, "user_id")


def sync_event_attendees_to_lms_batch(training_event: str) -> dict:
	"""Enroll Training Event attendees into the linked LMS Batch."""
	_require_lms()
	event = _get_event(training_event)

	if not event.get("lms_batch"):
		frappe.throw(_("Link an LMS Batch on Training Event before syncing attendees"))

	batch = event.lms_batch
	enrolled: list[str] = []
	skipped: list[str] = []

	for row in event.employees:
		user = _employee_user(row.employee)
		if not user:
			skipped.append(row.employee)
			continue

		if frappe.db.exists("LMS Batch Enrollment", {"batch": batch, "member": user}):
			skipped.append(user)
			continue

		frappe.get_doc(
			{
				"doctype": "LMS Batch Enrollment",
				"batch": batch,
				"member": user,
			}
		).insert(ignore_permissions=True)
		enrolled.append(user)

	return {"enrolled": enrolled, "skipped": skipped, "batch": batch}


def writeback_lms_completion_to_training_result(training_event: str) -> dict:
	"""Write LMS course progress back to Training Result for the event."""
	_require_lms()
	event = _get_event(training_event)

	if event.docstatus != 1:
		frappe.throw(_("Training Event must be submitted before syncing LMS completion"))

	course = event.get("lms_course")
	if not course:
		frappe.throw(_("Link an LMS Course on Training Event before syncing completion"))

	result_name = frappe.db.exists("Training Result", {"training_event": training_event})
	if result_name:
		result = frappe.get_doc("Training Result", result_name)
	else:
		result = frappe.new_doc("Training Result")
		result.training_event = training_event

	existing = {row.employee: row for row in result.employees}
	updated: list[str] = []

	for row in event.employees:
		user = _employee_user(row.employee)
		if not user:
			continue

		progress = frappe.db.get_value(
			"LMS Enrollment",
			{"course": course, "member": user},
			"progress",
		)
		progress = progress or 0
		is_complete = progress >= 100

		if row.employee in existing:
			emp_row = existing[row.employee]
		else:
			emp_row = result.append("employees", {"employee": row.employee})

		emp_row.hours = progress / 10
		emp_row.comments = f"LMS progress: {progress}%"
		if is_complete:
			emp_row.grade = "Completed"
			updated.append(row.employee)
		elif progress:
			emp_row.grade = "In Progress"

	if result.docstatus == 0 and result.employees:
		result.insert(ignore_permissions=True)
	elif result.docstatus == 0:
		result.save(ignore_permissions=True)
	else:
		result.save(ignore_permissions=True)

	return {"training_result": result.name, "completed_employees": updated}


def on_training_event_submit(doc, method=None):
	"""Auto-sync attendees when a submitted event has an LMS batch linked."""
	if not LMS_INSTALLED() or not doc.get("lms_batch") or not doc.employees:
		return

	try:
		sync_event_attendees_to_lms_batch(doc.name)
	except Exception:
		frappe.log_error(title="MCX HRMS LMS sync failed", message=frappe.get_traceback())
