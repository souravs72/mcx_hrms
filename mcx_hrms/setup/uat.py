# Copyright (c) 2026, Ascra Technologies LLP and contributors
# For license information, please see license.txt

"""UAT checklist runner — validates key MCX HRMS masters exist."""

from __future__ import annotations

import frappe

from mcx_hrms.constants import (
	BRANCHES,
	COMPANY_NAME,
	DEMO_EMPLOYEES,
	DEPARTMENTS,
	DESIGNATIONS,
	EMPLOYEE_GRADES,
	EXPENSE_CLAIM_TYPES,
	HOLIDAY_LIST_NAME,
	JOB_OPENING_TITLE,
	LEAVE_POLICY_TITLE,
	LEAVE_TYPES,
	LMS_BATCH_TITLE,
	LMS_COURSE_TITLE,
	SALARY_COMPONENTS,
	SALARY_STRUCTURE_NAME,
	SHIFT_TYPE_NAME,
	TRAINING_EVENT_NAME,
	TRAINING_PROGRAM_NAME,
)


def _check(label: str, passed: bool, detail: str = "") -> dict:
	return {"check": label, "passed": bool(passed), "detail": detail}


def run_uat_checklist(company: str | None = None) -> dict:
	"""Run UAT validation checks and return a structured report."""
	company = company or COMPANY_NAME
	checks: list[dict] = []

	checks.append(_check("Company MCX exists", frappe.db.exists("Company", company)))

	for branch in BRANCHES:
		checks.append(_check("Branch: " + branch, frappe.db.exists("Branch", branch)))

	for dept in DEPARTMENTS:
		checks.append(
			_check(
				f"Department: {dept}",
				frappe.db.exists("Department", {"department_name": dept, "company": company}),
			)
		)

	for designation in DESIGNATIONS:
		checks.append(
			_check("Designation: " + designation, frappe.db.exists("Designation", designation))
		)

	for grade in EMPLOYEE_GRADES:
		checks.append(_check("Employee Grade: " + grade, frappe.db.exists("Employee Grade", grade)))

	checks.append(_check("Holiday List", frappe.db.exists("Holiday List", HOLIDAY_LIST_NAME)))

	for lt in LEAVE_TYPES:
		checks.append(_check("Leave Type: " + lt["name"], frappe.db.exists("Leave Type", lt["name"])))

	checks.append(
		_check(
			"Leave Policy",
			bool(frappe.db.get_value("Leave Policy", {"title": LEAVE_POLICY_TITLE})),
		)
	)
	checks.append(_check("Shift Type", frappe.db.exists("Shift Type", SHIFT_TYPE_NAME)))

	for ect in EXPENSE_CLAIM_TYPES:
		checks.append(
			_check("Expense Claim Type: " + ect, frappe.db.exists("Expense Claim Type", ect))
		)

	for sc in SALARY_COMPONENTS:
		checks.append(
			_check("Salary Component: " + sc["name"], frappe.db.exists("Salary Component", sc["name"]))
		)

	checks.append(
		_check("Salary Structure", frappe.db.exists("Salary Structure", SALARY_STRUCTURE_NAME))
	)

	for emp in DEMO_EMPLOYEES:
		checks.append(
			_check(
				f"Demo employee: {emp['first_name']} {emp['last_name']}",
				frappe.db.exists("Employee", {"user_id": emp["email"]}),
			)
		)

	checks.append(
		_check(
			"Job Opening",
			bool(frappe.db.get_value("Job Opening", {"job_title": JOB_OPENING_TITLE})),
		)
	)
	checks.append(_check("Training Program", frappe.db.exists("Training Program", TRAINING_PROGRAM_NAME)))
	checks.append(_check("Training Event", frappe.db.exists("Training Event", TRAINING_EVENT_NAME)))

	if "lms" in frappe.get_installed_apps():
		checks.append(
			_check(
				"LMS Course",
				bool(frappe.db.get_value("LMS Course", {"title": LMS_COURSE_TITLE})),
			)
		)
		checks.append(
			_check(
				"LMS Batch",
				bool(frappe.db.get_value("LMS Batch", {"title": LMS_BATCH_TITLE})),
			)
		)

	checks.append(
		_check(
			"Job Requisition Workflow",
			frappe.db.exists("Workflow", "MCX Job Requisition Approval"),
		)
	)
	checks.append(
		_check(
			"Expense Claim Workflow",
			frappe.db.exists("Workflow", "MCX Expense Claim Approval"),
		)
	)
	checks.append(
		_check(
			"Leave Application Workflow",
			frappe.db.exists("Workflow", "MCX Leave Application Approval"),
		)
	)

	checks.append(
		_check(
			"Training Event LMS fields",
			frappe.db.exists("Custom Field", "Training Event-lms_course")
			and frappe.db.exists("Custom Field", "Training Event-lms_batch"),
		)
	)

	checks.append(
		_check(
			"Salary Structure Assignments",
			frappe.db.count("Salary Structure Assignment") >= len(DEMO_EMPLOYEES),
		)
	)
	from mcx_hrms.setup.hr_lifecycle import has_fy_2026_income_tax_slab

	checks.append(_check("Payroll Period FY 2026-27", frappe.db.exists("Payroll Period", "MCX Payroll FY 2026-27")))
	checks.append(_check("Income Tax Slab FY 2026-27", has_fy_2026_income_tax_slab()))
	checks.append(
		_check(
			"Appraisal Cycle",
			frappe.db.exists("Appraisal Cycle", "MCX Appraisal Cycle 2026"),
		)
	)
	checks.append(
		_check(
			"Employee Separation Template",
			bool(frappe.db.get_value("Employee Separation Template", {"title": "MCX Standard Separation"})),
		)
	)

	# Demo transaction readiness (client walkthrough)
	checks.append(
		_check(
			"Org hierarchy (reports_to)",
			frappe.db.count("Employee", {"company": company, "reports_to": ["is", "set"]}) >= 3,
		)
	)
	checks.append(_check("Leave Application samples", frappe.db.count("Leave Application") >= 1))
	checks.append(_check("Expense Claim samples", frappe.db.count("Expense Claim") >= 1))
	checks.append(_check("Employee Checkin samples", frappe.db.count("Employee Checkin") >= 1))
	checks.append(
		_check(
			"Attendance samples",
			frappe.db.count("Attendance", {"docstatus": 1}) >= 1,
		)
	)
	checks.append(
		_check(
			"Salary Slip samples",
			frappe.db.count("Salary Slip", {"docstatus": 1}) >= 1,
		)
	)
	checks.append(_check("Payroll Entry draft", frappe.db.count("Payroll Entry") >= 1))
	checks.append(_check("Appraisal sample", frappe.db.count("Appraisal") >= 1))
	checks.append(_check("Interview sample", frappe.db.count("Interview") >= 1))
	checks.append(_check("Job Offer sample", frappe.db.count("Job Offer") >= 1))
	checks.append(
		_check(
			"Employee Separation sample",
			frappe.db.count("Employee Separation") >= 1,
		)
	)
	checks.append(
		_check(
			"Employee Bank Account samples",
			frappe.db.count("Bank Account", {"party_type": "Employee"}) >= 1,
		)
	)

	if "mcx_learning_ai" in frappe.get_installed_apps():
		settings = frappe.get_single("MCX Learning AI Settings")
		checks.append(_check("MCX Learning AI enabled", bool(settings.enabled)))

	passed = sum(1 for c in checks if c["passed"])
	total = len(checks)

	return {
		"company": company,
		"passed": passed,
		"total": total,
		"success": passed == total,
		"checks": checks,
	}


def print_uat_report(company: str | None = None):
	"""Print UAT checklist to console (for bench execute)."""
	report = run_uat_checklist(company)
	print(f"\nMCX HRMS UAT Checklist — {report['passed']}/{report['total']} passed\n")
	for row in report["checks"]:
		status = "PASS" if row["passed"] else "FAIL"
		print(f"  [{status}] {row['check']}")
	print()
	return report
