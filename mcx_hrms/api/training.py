# Copyright (c) 2026, Ascra Technologies LLP and contributors
# For license information, please see license.txt

"""Whitelisted APIs for the LMS training bridge."""

from __future__ import annotations

import frappe

from mcx_hrms.mcx_hrms.training_bridge import (
	sync_event_attendees_to_lms_batch,
	writeback_lms_completion_to_training_result,
)


@frappe.whitelist()
def sync_attendees_to_lms(training_event: str) -> dict:
	"""Enroll Training Event attendees into the linked LMS Batch."""
	return sync_event_attendees_to_lms_batch(training_event)


@frappe.whitelist()
def sync_lms_completion(training_event: str) -> dict:
	"""Write LMS progress back to Training Result."""
	return writeback_lms_completion_to_training_result(training_event)


@frappe.whitelist()
def sync_training(training_event: str) -> dict:
	"""Full sync: enroll attendees then write back completion."""
	enrollment = sync_event_attendees_to_lms_batch(training_event)
	completion = writeback_lms_completion_to_training_result(training_event)
	return {"enrollment": enrollment, "completion": completion}
