# Copyright (c) 2026, Ascra Technologies LLP and contributors
# For license information, please see license.txt

"""HR lifecycle, payroll and PMS demo seed (idempotent)."""

from __future__ import annotations

import frappe
from frappe.utils import add_months, get_first_day, get_last_day, getdate, today

from mcx_hrms.constants import (
	LEAVE_POLICY_TITLE,
	SALARY_STRUCTURE_NAME,
	SHIFT_TYPE_NAME,
)

LEAVE_PERIOD_NAME = "MCX Leave Period 2026"
PAYROLL_PERIOD_NAME = "MCX Payroll FY 2026-27"
INCOME_TAX_SLAB_2026 = "New Tax Regime: 2026-2027"
APPRAISAL_CYCLE_NAME = "MCX Appraisal Cycle 2026"
SEPARATION_TEMPLATE_NAME = "MCX Standard Separation"


def ensure_holiday_list_assignment(company: str, holiday_list: str | None = None):
	"""Native Holiday List Assignment for Company — required by hrms.utils.holiday_list."""
	from mcx_hrms.constants import HOLIDAY_LIST_NAME

	holiday_list = holiday_list or HOLIDAY_LIST_NAME
	if not frappe.db.exists("DocType", "Holiday List Assignment"):
		return
	if not frappe.db.exists("Holiday List", holiday_list):
		return

	year = getdate(today()).year
	from_date = f"{year}-01-01"
	existing = frappe.db.get_value(
		"Holiday List Assignment",
		{
			"applicable_for": "Company",
			"assigned_to": company,
			"holiday_list": holiday_list,
			"docstatus": ["<", 2],
		},
		["name", "docstatus"],
		as_dict=True,
	)
	if existing:
		if existing.docstatus == 0:
			frappe.get_doc("Holiday List Assignment", existing.name).submit()
		return

	hla = frappe.get_doc(
		{
			"doctype": "Holiday List Assignment",
			"applicable_for": "Company",
			"assigned_to": company,
			"holiday_list": holiday_list,
			"from_date": from_date,
		}
	)
	hla.insert(ignore_permissions=True)
	hla.submit()


def ensure_hr_lifecycle_demo(company: str, employees: list[str]):
	"""Seed leave, attendance, payroll, PMS and separation demo masters."""
	ensure_leave_period_and_allocations(company, employees)
	ensure_shift_assignments(employees)
	ensure_salary_structure_assignments(company, employees)
	ensure_payroll_period(company)
	ensure_income_tax_slab_2026_27()
	ensure_pms_masters(company)
	ensure_separation_template(company)


def ensure_leave_period_and_allocations(company: str, employees: list[str]):
	"""Assign leave via native Leave Policy Assignment submit (creates allocations)."""
	year = getdate(today()).year
	from_date = f"{year}-01-01"
	to_date = f"{year}-12-31"

	leave_period = frappe.db.get_value(
		"Leave Period",
		{"company": company, "from_date": from_date, "to_date": to_date},
	)
	if not leave_period:
		leave_period = frappe.get_doc(
			{
				"doctype": "Leave Period",
				"from_date": from_date,
				"to_date": to_date,
				"company": company,
				"is_active": 1,
			}
		).insert(ignore_permissions=True).name

	leave_policy = frappe.db.get_value("Leave Policy", {"title": LEAVE_POLICY_TITLE})
	if not leave_policy:
		return

	# Leave Policy must be submitted before Leave Policy Assignment
	policy_doc = frappe.get_doc("Leave Policy", leave_policy)
	if policy_doc.docstatus == 0:
		policy_doc.submit()

	for employee in employees:
		existing = frappe.db.get_value(
			"Leave Policy Assignment",
			{"employee": employee, "leave_policy": leave_policy},
			["name", "docstatus"],
			as_dict=True,
		)
		if existing:
			if existing.docstatus == 0:
				# Only submit if allocations were not already created manually
				has_alloc = frappe.db.exists(
					"Leave Allocation",
					{"employee": employee, "from_date": from_date, "to_date": to_date, "docstatus": 1},
				)
				if not has_alloc:
					try:
						frappe.get_doc("Leave Policy Assignment", existing.name).submit()
					except Exception:
						# OverlapError / already allocated — treat as seeded
						frappe.clear_messages()
			continue

		try:
			lpa = frappe.get_doc(
				{
					"doctype": "Leave Policy Assignment",
					"employee": employee,
					"leave_policy": leave_policy,
					"assignment_based_on": "Leave Period",
					"leave_period": leave_period,
					"effective_from": from_date,
				}
			)
			lpa.insert(ignore_permissions=True)
			lpa.submit()
		except Exception:
			frappe.clear_messages()
			continue


def ensure_shift_assignments(employees: list[str]):
	"""Native Shift Assignment must be submitted for attendance/checkin shift resolution."""
	start = get_first_day(today())
	for employee in employees:
		existing = frappe.db.get_value(
			"Shift Assignment",
			{"employee": employee, "shift_type": SHIFT_TYPE_NAME, "start_date": start},
			["name", "docstatus"],
			as_dict=True,
		)
		if existing:
			if existing.docstatus == 0:
				frappe.get_doc("Shift Assignment", existing.name).submit()
			continue

		doc = frappe.get_doc(
			{
				"doctype": "Shift Assignment",
				"employee": employee,
				"shift_type": SHIFT_TYPE_NAME,
				"start_date": start,
				"status": "Active",
			}
		)
		doc.insert(ignore_permissions=True)
		doc.submit()


def ensure_salary_structure_assignments(company: str, employees: list[str]):
	if not frappe.db.exists("Salary Structure", SALARY_STRUCTURE_NAME):
		return

	# Cover current India FY so prior-month salary slips and payroll entry both resolve
	fy_start = frappe.db.get_value(
		"Fiscal Year",
		{"disabled": 0},
		"year_start_date",
		order_by="year_start_date desc",
	)
	from_date = getdate(fy_start) if fy_start else getdate(f"{getdate(today()).year}-04-01")
	base_by_grade = {"Grade A": 80000, "Grade B": 64000, "Grade C": 48000}

	for employee in employees:
		existing = frappe.db.get_value(
			"Salary Structure Assignment",
			{"employee": employee, "salary_structure": SALARY_STRUCTURE_NAME, "docstatus": ["<", 2]},
			["name", "docstatus"],
			as_dict=True,
		)
		if existing:
			if existing.docstatus == 0:
				frappe.get_doc("Salary Structure Assignment", existing.name).submit()
			continue

		grade = frappe.db.get_value("Employee", employee, "grade") or "Grade B"
		base = base_by_grade.get(grade, 64000)

		doc = frappe.get_doc(
			{
				"doctype": "Salary Structure Assignment",
				"employee": employee,
				"salary_structure": SALARY_STRUCTURE_NAME,
				"company": company,
				"from_date": from_date,
				"base": base,
				"currency": "INR",
				"income_tax_slab": _preferred_income_tax_slab(),
				"employment_state": "Maharashtra",
			}
		)
		doc.insert(ignore_permissions=True)
		doc.submit()


FY_2026_TAX_SLABS = (
	INCOME_TAX_SLAB_2026,
	"India - New Regime FY 2026-27",
	"New Tax Regime FY 2026-27",
)


def has_fy_2026_income_tax_slab() -> bool:
	return any(frappe.db.exists("Income Tax Slab", name) for name in FY_2026_TAX_SLABS)


def _preferred_income_tax_slab() -> str | None:
	for name in (
		*FY_2026_TAX_SLABS,
		"New Tax Regime: 2025-2026",
		"India - New Regime FY 2025-26",
		"New Tax Regime: 2024-2025",
	):
		if frappe.db.exists("Income Tax Slab", name):
			return name
	# Any submitted slab is better than none for SSA
	return frappe.db.get_value("Income Tax Slab", {"disabled": 0, "docstatus": 1}, "name")


def ensure_payroll_period(company: str):
	if frappe.db.exists("Payroll Period", PAYROLL_PERIOD_NAME):
		return

	frappe.get_doc(
		{
			"doctype": "Payroll Period",
			"name": PAYROLL_PERIOD_NAME,
			"company": company,
			"start_date": "2026-04-01",
			"end_date": "2027-03-31",
		}
	).insert(ignore_permissions=True)


def ensure_income_tax_slab_2026_27():
	"""Demo placeholder for FY 2026-27 — validate against notified slabs before production."""
	if has_fy_2026_income_tax_slab():
		return

	for source in (
		"New Tax Regime: 2025-2026",
		"India - New Regime FY 2025-26",
		"New Tax Regime: 2024-2025",
	):
		if not frappe.db.exists("Income Tax Slab", source):
			continue
		src = frappe.get_doc("Income Tax Slab", source)
		doc = frappe.copy_doc(src)
		doc.name = INCOME_TAX_SLAB_2026
		doc.effective_from = "2026-04-01"
		doc.docstatus = 0
		doc.insert(ignore_permissions=True)
		doc.submit()
		return


def ensure_pms_masters(company: str):
	kras = [
		(
			"Order & trade execution quality",
			"Accuracy of order handling, turnaround on member requests, and exception escalation.",
		),
		(
			"Settlement discipline",
			"On-time pay-in/pay-out coordination and reduction of settlement breaks.",
		),
		(
			"Regulatory & compliance adherence",
			"Timely reporting, KYC hygiene, and zero critical compliance findings.",
		),
		(
			"Collaboration & process improvement",
			"Cross-desk coordination with Clearing, IT and Compliance; documented SOPs.",
		),
	]
	for title, description in kras:
		if not frappe.db.exists("KRA", title):
			frappe.get_doc(
				{"doctype": "KRA", "title": title, "description": description}
			).insert(ignore_permissions=True)

	if not frappe.db.exists("Appraisal Template", "MCX Annual Appraisal Template"):
		template = frappe.get_doc(
			{
				"doctype": "Appraisal Template",
				"template_title": "MCX Annual Appraisal Template",
				"description": "Annual performance review framework for MCX operations staff.",
				"kra_evaluation_method": "Manual Rating",
				"rate_goals_manually": 1,
				"goals": [
					{"key_result_area": kras[0][0], "per_weightage": 30},
					{"key_result_area": kras[1][0], "per_weightage": 25},
					{"key_result_area": kras[2][0], "per_weightage": 25},
					{"key_result_area": kras[3][0], "per_weightage": 20},
				],
			}
		)
		template.insert(ignore_permissions=True)

	if frappe.db.exists("Appraisal Cycle", APPRAISAL_CYCLE_NAME):
		# Soften older demo wording
		frappe.db.set_value(
			"Appraisal Cycle",
			APPRAISAL_CYCLE_NAME,
			"description",
			"FY performance cycle for Trading, Clearing, IT and Compliance teams.",
			update_modified=False,
		)
		return

	cycle = frappe.get_doc(
		{
			"doctype": "Appraisal Cycle",
			"cycle_name": APPRAISAL_CYCLE_NAME,
			"company": company,
			"start_date": get_first_day(today()),
			"end_date": get_last_day(add_months(today(), 11)),
			"description": "FY performance cycle for Trading, Clearing, IT and Compliance teams.",
			"kra_evaluation_method": "Manual Rating",
			"status": "In Progress",
		}
	)
	cycle.insert(ignore_permissions=True)


def ensure_separation_template(company: str):
	if frappe.db.get_value("Employee Separation Template", {"title": SEPARATION_TEMPLATE_NAME}):
		return

	doc = frappe.get_doc(
		{
			"doctype": "Employee Separation Template",
			"title": SEPARATION_TEMPLATE_NAME,
			"company": company,
			"department": frappe.db.get_value(
				"Department", {"department_name": "Human Resources", "company": company}
			),
			"designation": "HR Executive",
			"activities": [
				{
					"activity_name": "Return company assets",
					"description": "Collect laptop, ID card and access tokens.",
				},
				{
					"activity_name": "Revoke system access",
					"description": "Disable ERP, LMS and email access.",
				},
				{
					"activity_name": "Full and Final settlement",
					"description": "Process F&F and gratuity where applicable.",
				},
			],
		}
	)
	doc.insert(ignore_permissions=True)
