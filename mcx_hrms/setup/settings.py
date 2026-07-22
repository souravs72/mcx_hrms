# Copyright (c) 2026, Ascra Technologies LLP and contributors
# For license information, please see license.txt

"""Configure HR/Payroll/LMS singleton settings for MCX demo."""

from __future__ import annotations

import frappe


def ensure_singleton_settings(company: str | None = None):
	company = company or frappe.db.get_single_value("Global Defaults", "default_company")
	if not company:
		return

	_ensure_hr_settings()
	_ensure_payroll_settings()
	_ensure_lms_settings()
	frappe.db.commit()


def _ensure_hr_settings():
	if not frappe.db.exists("DocType", "HR Settings"):
		return
	hs = frappe.get_single("HR Settings")
	updates = {
		"emp_created_by": "Naming Series",
		"retirement_age": "60",
		"standard_working_hours": "8",
		"leave_approver_mandatory_in_leave_application": 1,
		"expense_approver_mandatory_in_expense_claim": 1,
		"prevent_self_leave_approval": 1,
		"prevent_self_expense_approval": 1,
		"allow_multiple_shift_assignments": 1,
		"allow_employee_checkin_from_mobile_app": 1,
		# Desk/demo seed checkins without GPS; production can re-enable
		"allow_geolocation_tracking": 0,
	}
	for key, val in updates.items():
		if hasattr(hs, key):
			hs.set(key, val)
	hs.save(ignore_permissions=True)


def _ensure_payroll_settings():
	if not frappe.db.exists("DocType", "Payroll Settings"):
		return
	ps = frappe.get_single("Payroll Settings")
	updates = {
		"payroll_based_on": "Leave",
		"consider_unmarked_attendance_as": "Present",
		"include_holidays_in_total_working_days": 1,
		"max_working_hours_against_timesheet": 0,
		"email_salary_slip_to_employee": 0,
		"encrypt_salary_slips_in_emails": 0,
		"process_payroll_accounting_entry_based_on_employee": 1,
	}
	for key, val in updates.items():
		if hasattr(ps, key):
			ps.set(key, val)
	# India Payroll toggles (custom fields from india_payroll app)
	for key in ("enable_epf", "enable_esic", "enable_professional_tax", "enable_lwf"):
		if hasattr(ps, key):
			ps.set(key, 1)
	ps.save(ignore_permissions=True)


def _ensure_lms_settings():
	if "lms" not in frappe.get_installed_apps():
		return
	if not frappe.db.exists("DocType", "LMS Settings"):
		return
	ls = frappe.get_single("LMS Settings")
	updates = {
		"allow_guest_access": 0,
		"disable_signup": 0,
		"prevent_skipping_videos": 0,
		"send_calendar_invite_for_evaluator": 0,
	}
	for key, val in updates.items():
		if hasattr(ls, key):
			ls.set(key, val)
	_ensure_ai_learning_sidebar(ls)
	ls.save(ignore_permissions=True)


def _ensure_ai_learning_sidebar(lms_settings):
	"""Add AI Learning link to LMS sidebar when Web Page exists."""
	route = "/ai-learning"
	for row in lms_settings.get("sidebar_items") or []:
		if row.route == route or row.title == "AI Learning":
			return

	try:
		web_page = frappe.db.get_value("Web Page", {"route": "ai-learning"})
		if not web_page:
			web_page = _ensure_ai_learning_web_page()

		lms_settings.append(
			"sidebar_items",
			{
				"web_page": web_page,
				"title": "AI Learning",
				"route": route,
				"icon": "sparkles",
			},
		)
	except Exception:
		frappe.log_error(title="MCX HRMS LMS sidebar setup failed")


def _ensure_ai_learning_web_page() -> str:
	existing = frappe.db.get_value("Web Page", {"route": "ai-learning"})
	if existing:
		return existing

	doc = frappe.get_doc(
		{
			"doctype": "Web Page",
			"title": "AI Learning",
			"route": "ai-learning",
			"published": 1,
			"content_type": "Page Builder",
			"page_blocks": [
				{
					"web_template": "Section with Cards",
					"web_template_values": frappe.as_json(
						{
							"title": "MCX Learning AI",
							"subtitle": "Personalized recommendations, path curation and grounded search.",
							"card_1_title": "Open AI Learning",
							"card_1_content": "Continue to the MCX AI learning workspace.",
							"card_1_link": "/ai-learning",
						}
					),
				}
			],
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name
