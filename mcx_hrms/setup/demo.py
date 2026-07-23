# Copyright (c) 2026, Ascra Technologies LLP and contributors
# For license information, please see license.txt

"""Comprehensive demo seed for mcx.site (idempotent)."""

from __future__ import annotations

from datetime import timedelta

import frappe
from frappe.utils import add_days, getdate, now_datetime, today

from mcx_hrms.constants import (
	BRANCHES,
	COMPANY_ABBR,
	COMPANY_NAME,
	DEMO_EMPLOYEES,
	DEMO_SITE,
	DEMO_USER_PASSWORD,
	DEPARTMENTS,
	DESIGNATIONS,
	EMPLOYEE_GRADES,
	EXPENSE_APPROVAL_ROLES,
	EXPENSE_CLAIM_TYPES,
	HOLIDAY_LIST_NAME,
	JOB_APPLICANT_EMAIL,
	JOB_APPLICANT_NAME,
	JOB_OPENING_TITLE,
	LEAVE_POLICY_TITLE,
	LEAVE_TYPES,
	LEGACY_JOB_APPLICANT_NAME,
	LEGACY_JOB_OPENING_TITLE,
	LEGACY_LMS_BATCH_TITLE,
	LEGACY_TRAINING_EVENT_NAME,
	LMS_BATCH_TITLE,
	LMS_COURSE_TITLE,
	SALARY_COMPONENTS,
	SALARY_STRUCTURE_NAME,
	SHIFT_TYPE_NAME,
	TRAINING_EVENT_NAME,
	TRAINING_PROGRAM_NAME,
)
from mcx_hrms.setup.hr_lifecycle import ensure_hr_lifecycle_demo


def _conf_flag(key: str) -> bool | None:
	"""Parse site_config flags. bench set-config stores 1/0, not True/False."""
	val = frappe.local.conf.get(key)
	if val is None:
		return None
	if isinstance(val, str):
		lower = val.strip().lower()
		if lower in {"0", "false", "no", "off"}:
			return False
		if lower in {"1", "true", "yes", "on"}:
			return True
	return bool(val)


def is_demo_site() -> bool:
	"""Demo seed runs on mcx.site by default; override via site_config."""
	flag = _conf_flag("mcx_hrms_demo_mode")
	if flag is False:
		return False
	if flag is True:
		return True
	return frappe.local.site == DEMO_SITE


def setup_demo_site():
	"""Seed MCX HRMS demo data (install / mcx.site only)."""
	if not is_demo_site():
		return
	if "hrms" not in frappe.get_installed_apps():
		return

	company = ensure_company()
	ensure_branches()
	ensure_departments(company)
	ensure_designations()
	ensure_employee_grades()
	ensure_holiday_list(company)
	ensure_leave_types()
	ensure_leave_policy(company)
	ensure_shift_type()
	ensure_expense_claim_types()
	ensure_salary_components()
	ensure_salary_structure(company)
	employees = ensure_demo_employees(company)
	ensure_hr_lifecycle_demo(company, employees)
	ensure_job_opening_and_applicant(company)
	ensure_training_and_lms(company, employees)

	# Sample transactions for client walkthrough (native HRMS docs)
	from mcx_hrms.setup.transactions import seed_demo_transactions

	seed_demo_transactions(company)


def ensure_company() -> str:
	if frappe.db.exists("Company", COMPANY_NAME):
		return COMPANY_NAME

	if "erpnext" not in frappe.get_installed_apps():
		return frappe.defaults.get_global_default("company") or ""

	doc = frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": COMPANY_NAME,
			"abbr": COMPANY_ABBR,
			"default_currency": "INR",
			"country": "India",
			"create_chart_of_accounts_based_on": "Standard Template",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def ensure_branches():
	for branch in BRANCHES:
		if frappe.db.exists("Branch", branch):
			continue
		frappe.get_doc({"doctype": "Branch", "branch": branch}).insert(ignore_permissions=True)


def ensure_departments(company: str):
	for dept in DEPARTMENTS:
		if frappe.db.exists("Department", {"department_name": dept, "company": company}):
			continue
		frappe.get_doc(
			{"doctype": "Department", "department_name": dept, "company": company}
		).insert(ignore_permissions=True)


def ensure_designations():
	for designation in DESIGNATIONS:
		if frappe.db.exists("Designation", designation):
			continue
		frappe.get_doc({"doctype": "Designation", "designation_name": designation}).insert(
			ignore_permissions=True
		)


def ensure_employee_grades():
	for grade in EMPLOYEE_GRADES:
		if frappe.db.exists("Employee Grade", grade):
			continue
		frappe.get_doc(
			{
				"doctype": "Employee Grade",
				"name": grade,
				"__newname__": grade,
				"default_base_pay": 500000,
			}
		).insert(ignore_permissions=True)


def ensure_holiday_list(company: str):
	year = getdate(today()).year
	holidays = _india_holidays_for_year(year)

	if not frappe.db.exists("Holiday List", HOLIDAY_LIST_NAME):
		doc = frappe.get_doc(
			{
				"doctype": "Holiday List",
				"holiday_list_name": HOLIDAY_LIST_NAME,
				"from_date": f"{year}-01-01",
				"to_date": f"{year}-12-31",
				"weekly_off": "Sunday",
				"holidays": holidays,
			}
		)
		doc.insert(ignore_permissions=True)
	else:
		# Backfill missing public holidays on existing list
		doc = frappe.get_doc("Holiday List", HOLIDAY_LIST_NAME)
		existing = {str(getdate(h.holiday_date)) for h in doc.holidays}
		added = False
		for row in holidays:
			if row["holiday_date"] not in existing:
				doc.append("holidays", row)
				added = True
		if added:
			doc.save(ignore_permissions=True)

	if frappe.db.exists("Company", company):
		frappe.db.set_value("Company", company, "default_holiday_list", HOLIDAY_LIST_NAME)

	# HRMS v16+ resolves holidays via Holiday List Assignment (not only Employee.holiday_list)
	from mcx_hrms.setup.hr_lifecycle import ensure_holiday_list_assignment

	ensure_holiday_list_assignment(company)


def _india_holidays_for_year(year: int) -> list[dict]:
	"""National + common Maharashtra/TN market holidays for a polished calendar."""
	return [
		{"holiday_date": f"{year}-01-26", "description": "Republic Day"},
		{"holiday_date": f"{year}-03-14", "description": "Holi"},
		{"holiday_date": f"{year}-04-03", "description": "Good Friday"},
		{"holiday_date": f"{year}-04-14", "description": "Dr. Ambedkar Jayanti"},
		{"holiday_date": f"{year}-05-01", "description": "Maharashtra Day"},
		{"holiday_date": f"{year}-08-15", "description": "Independence Day"},
		{"holiday_date": f"{year}-08-27", "description": "Ganesh Chaturthi"},
		{"holiday_date": f"{year}-10-02", "description": "Gandhi Jayanti"},
		{"holiday_date": f"{year}-10-20", "description": "Dussehra"},
		{"holiday_date": f"{year}-11-08", "description": "Diwali"},
		{"holiday_date": f"{year}-11-09", "description": "Diwali (Balipratipada)"},
		{"holiday_date": f"{year}-12-25", "description": "Christmas"},
	]


def ensure_leave_types():
	for spec in LEAVE_TYPES:
		if frappe.db.exists("Leave Type", spec["name"]):
			continue
		frappe.get_doc(
			{
				"doctype": "Leave Type",
				"leave_type_name": spec["name"],
				"max_leaves_allowed": spec["max_leaves_allowed"],
				"is_carry_forward": spec.get("is_carry_forward", 0),
			}
		).insert(ignore_permissions=True)


def ensure_leave_policy(company: str):
	existing = frappe.db.get_value(
		"Leave Policy", {"title": LEAVE_POLICY_TITLE}, ["name", "docstatus"], as_dict=True
	)
	if existing:
		if existing.docstatus == 0:
			frappe.get_doc("Leave Policy", existing.name).submit()
		return

	doc = frappe.get_doc(
		{
			"doctype": "Leave Policy",
			"title": LEAVE_POLICY_TITLE,
			"leave_policy_details": [
				{"leave_type": lt["name"], "annual_allocation": lt["max_leaves_allowed"]} for lt in LEAVE_TYPES
			],
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()


def ensure_shift_type():
	if frappe.db.exists("Shift Type", SHIFT_TYPE_NAME):
		return

	frappe.get_doc(
		{
			"doctype": "Shift Type",
			"name": SHIFT_TYPE_NAME,
			"start_time": "09:00:00",
			"end_time": "18:00:00",
			"color": "Blue",
		}
	).insert(ignore_permissions=True)


def ensure_expense_claim_types():
	for claim_type in EXPENSE_CLAIM_TYPES:
		if frappe.db.exists("Expense Claim Type", claim_type):
			continue
		frappe.get_doc({"doctype": "Expense Claim Type", "expense_type": claim_type}).insert(
			ignore_permissions=True
		)


def ensure_salary_components():
	for spec in SALARY_COMPONENTS:
		if frappe.db.exists("Salary Component", spec["name"]):
			continue
		frappe.get_doc(
			{
				"doctype": "Salary Component",
				"salary_component": spec["name"],
				"salary_component_abbr": spec["salary_component_abbr"],
				"type": spec["type"],
			}
		).insert(ignore_permissions=True)


def ensure_salary_structure(company: str):
	existing = frappe.db.get_value(
		"Salary Structure", SALARY_STRUCTURE_NAME, ["name", "docstatus"], as_dict=True
	)
	if existing:
		if existing.docstatus == 0:
			frappe.get_doc("Salary Structure", SALARY_STRUCTURE_NAME).submit()
		return

	components = []
	for spec in SALARY_COMPONENTS:
		if spec["type"] != "Earning":
			continue
		amount = {"Basic": 40000, "House Rent Allowance": 16000, "Special Allowance": 8000}.get(
			spec["name"], 5000
		)
		components.append(
			{
				"salary_component": spec["name"],
				"abbr": spec["salary_component_abbr"],
				"amount": amount,
				"amount_based_on_formula": 0,
			}
		)

	doc = frappe.get_doc(
		{
			"doctype": "Salary Structure",
			"name": SALARY_STRUCTURE_NAME,
			"company": company,
			"is_active": "Yes",
			"currency": "INR",
			"payroll_frequency": "Monthly",
			"earnings": components,
		}
	)
	doc.insert(ignore_permissions=True)
	doc.submit()


def ensure_user(email: str, first_name: str, last_name: str, roles: list[str] | None = None):
	if frappe.db.exists("User", email):
		user = frappe.get_doc("User", email)
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": first_name,
				"last_name": last_name,
				"send_welcome_email": 0,
				"user_type": "System User",
			}
		)
		user.new_password = DEMO_USER_PASSWORD
		user.insert(ignore_permissions=True)

	for role in roles or ["Employee", "Leave Approver"]:
		if role not in frappe.get_roles(email):
			user.add_roles(role)

	return email


def ensure_demo_employees(company: str) -> list[str]:
	employee_ids: list[str] = []
	hr_manager_email = DEMO_EMPLOYEES[0]["email"]

	for spec in DEMO_EMPLOYEES:
		roles = ["Employee"]
		if spec["designation"] == "HR Manager":
			roles.extend(["HR Manager", "HR User", "Leave Approver", "Expense Approver"])
			roles.extend(EXPENSE_APPROVAL_ROLES)
		elif spec["email"] == DEMO_EMPLOYEES[1]["email"]:
			roles.append("Leave Approver")

		ensure_user(spec["email"], spec["first_name"], spec["last_name"], roles)

		dept = frappe.db.get_value("Department", {"department_name": spec["department"], "company": company})
		existing = frappe.db.get_value(
			"Employee",
			{"user_id": spec["email"]},
			["name", "company"],
			as_dict=True,
		)
		if existing:
			# User↔Employee is 1:1; on shared UAT sites rehome Ascra (or other) demo
			# employees onto the MCX company instead of mixing companies in SSA.
			if existing.company != company:
				_rehome_demo_employee(existing.name, company, dept, spec, hr_manager_email)
			else:
				_polish_employee_profile(existing.name, company, dept, spec, hr_manager_email)
			employee_ids.append(existing.name)
			continue

		doc = frappe.get_doc(_employee_payload(company, dept, spec, hr_manager_email))
		# Hierarchy: non-HR employees report to Priya (HR Manager)
		if spec["email"] != hr_manager_email:
			hr_emp = frappe.db.get_value("Employee", {"user_id": hr_manager_email})
			if hr_emp:
				doc.reports_to = hr_emp
		doc.insert(ignore_permissions=True)
		employee_ids.append(doc.name)

	return employee_ids


def _employee_payload(company: str, department: str | None, spec: dict, hr_manager_email: str) -> dict:
	return {
		"doctype": "Employee",
		"first_name": spec["first_name"],
		"last_name": spec["last_name"],
		"employee_name": f"{spec['first_name']} {spec['last_name']}",
		"company": company,
		"user_id": spec["email"],
		"company_email": spec["email"],
		"prefered_contact_email": "Company Email",
		"prefered_email": spec["email"],
		"date_of_birth": spec.get("date_of_birth") or "1990-01-15",
		"date_of_joining": spec.get("date_of_joining") or "2020-04-01",
		"cell_number": spec.get("cell_number"),
		"permanent_address": spec.get("permanent_address"),
		"current_address": spec.get("current_address"),
		"department": department,
		"designation": spec["designation"],
		"branch": spec["branch"],
		"grade": spec["grade"],
		"gender": spec["gender"],
		"status": "Active",
		"holiday_list": HOLIDAY_LIST_NAME,
		"leave_approver": hr_manager_email,
		"expense_approver": hr_manager_email,
		"salary_mode": "Bank",
	}


def _polish_employee_profile(
	employee: str,
	company: str,
	department: str | None,
	spec: dict,
	hr_manager_email: str,
) -> None:
	"""Refresh profile fields so older thin seeds look production-ready."""
	doc = frappe.get_doc("Employee", employee)
	payload = _employee_payload(company, department, spec, hr_manager_email)
	for key, val in payload.items():
		if key in {"doctype", "user_id", "company"} or val in (None, ""):
			continue
		if hasattr(doc, key):
			doc.set(key, val)
	if spec["email"] != hr_manager_email:
		hr_emp = frappe.db.get_value("Employee", {"user_id": hr_manager_email, "company": company})
		if hr_emp and hr_emp != employee:
			doc.reports_to = hr_emp
	doc.save(ignore_permissions=True)


def _rehome_demo_employee(
	employee: str,
	company: str,
	department: str | None,
	spec: dict,
	hr_manager_email: str,
) -> None:
	"""Move an existing @mcx.demo employee onto the demo company and refresh profile."""
	_polish_employee_profile(employee, company, department, spec, hr_manager_email)
	doc = frappe.get_doc("Employee", employee)
	doc.company = company
	doc.save(ignore_permissions=True)


def ensure_job_opening_and_applicant(company: str):
	if not frappe.db.exists("Designation", "Trading Executive"):
		return

	# Rename legacy demo-titled opening if present
	legacy_opening = frappe.db.get_value("Job Opening", {"job_title": LEGACY_JOB_OPENING_TITLE})
	if legacy_opening and not frappe.db.exists("Job Opening", {"job_title": JOB_OPENING_TITLE}):
		frappe.db.set_value("Job Opening", legacy_opening, "job_title", JOB_OPENING_TITLE)

	opening = frappe.db.get_value("Job Opening", {"job_title": JOB_OPENING_TITLE})
	jd = (
		"<p><b>Role overview</b></p>"
		"<p>Execute and monitor trades on the MCX commodity desk, support member queries, "
		"and ensure order-to-settlement hygiene in line with exchange rules.</p>"
		"<p><b>Key responsibilities</b></p>"
		"<ul>"
		"<li>Order entry, modifications and cancellations on the trading platform</li>"
		"<li>Intraday monitoring of positions, margins and market alerts</li>"
		"<li>Coordination with Clearing &amp; Settlement and Compliance on exceptions</li>"
		"<li>Member onboarding support for trading workflows</li>"
		"</ul>"
		"<p><b>Requirements</b></p>"
		"<ul>"
		"<li>2–5 years in exchange / brokerage trading operations</li>"
		"<li>Working knowledge of commodity derivatives and risk limits</li>"
		"<li>Strong communication skills for member-facing work</li>"
		"</ul>"
	)
	if not opening:
		opening = frappe.get_doc(
			{
				"doctype": "Job Opening",
				"job_title": JOB_OPENING_TITLE,
				"designation": "Trading Executive",
				"company": company,
				"department": frappe.db.get_value(
					"Department", {"department_name": "Trading Operations", "company": company}
				),
				"description": jd,
				"status": "Open",
				"publish": 1,
			}
		).insert(ignore_permissions=True).name
	else:
		frappe.db.set_value("Job Opening", opening, "description", jd)

	legacy_applicant = frappe.db.get_value("Job Applicant", {"applicant_name": LEGACY_JOB_APPLICANT_NAME})
	if legacy_applicant and not frappe.db.exists("Job Applicant", {"applicant_name": JOB_APPLICANT_NAME}):
		frappe.db.set_value("Job Applicant", legacy_applicant, "applicant_name", JOB_APPLICANT_NAME)
		frappe.db.set_value("Job Applicant", legacy_applicant, "email_id", JOB_APPLICANT_EMAIL)

	if frappe.db.exists("Job Applicant", {"applicant_name": JOB_APPLICANT_NAME}):
		applicant = frappe.db.get_value("Job Applicant", {"applicant_name": JOB_APPLICANT_NAME})
		if opening and not frappe.db.get_value("Job Applicant", applicant, "job_title"):
			frappe.db.set_value("Job Applicant", applicant, "job_title", opening)
		return

	frappe.get_doc(
		{
			"doctype": "Job Applicant",
			"applicant_name": JOB_APPLICANT_NAME,
			"email_id": JOB_APPLICANT_EMAIL,
			"phone_number": "+91-9876501234",
			"designation": "Trading Executive",
			"job_title": opening,
			"status": "Open",
			"cover_letter": (
				"I bring four years of commodity desk experience across futures order management "
				"and member support, and am keen to contribute to MCX Trading Operations."
			),
		}
	).insert(ignore_permissions=True)


def ensure_training_and_lms(company: str, employees: list[str]):
	if not frappe.db.exists("Training Program", TRAINING_PROGRAM_NAME):
		program = frappe.get_doc(
			{
				"doctype": "Training Program",
				"training_program": TRAINING_PROGRAM_NAME,
				"company": company,
				"description": "Mandatory compliance and regulatory readiness programme for MCX staff.",
				"status": "Scheduled",
			}
		)
		program.insert(ignore_permissions=True)

	course_name = None
	batch_name = None
	if "lms" in frappe.get_installed_apps():
		course_name = ensure_lms_course()
		batch_name = ensure_lms_batch(course_name)

	# Rename legacy training event title if present
	if frappe.db.exists("Training Event", LEGACY_TRAINING_EVENT_NAME) and not frappe.db.exists(
		"Training Event", TRAINING_EVENT_NAME
	):
		frappe.rename_doc("Training Event", LEGACY_TRAINING_EVENT_NAME, TRAINING_EVENT_NAME, force=True)

	if frappe.db.exists("Training Event", TRAINING_EVENT_NAME):
		return

	start = now_datetime() + timedelta(days=7)
	end = start + timedelta(hours=4)
	event = frappe.get_doc(
		{
			"doctype": "Training Event",
			"event_name": TRAINING_EVENT_NAME,
			"training_program": TRAINING_PROGRAM_NAME,
			"event_status": "Scheduled",
			"type": "Seminar",
			"level": "Beginner",
			"company": company,
			"trainer_name": "MCX Compliance Team",
			"trainer_email": "training@mcx.demo",
			"course": LMS_COURSE_TITLE,
			"location": "Mumbai HQ — Conference Room A",
			"start_time": start,
			"end_time": end,
			"introduction": (
				"Quarterly SEBI / exchange compliance refresher covering reporting obligations, "
				"KYC hygiene and desk escalation protocols."
			),
		}
	)
	# Optional LMS links when fields exist
	if course_name and hasattr(event, "lms_course"):
		event.lms_course = course_name
	if batch_name and hasattr(event, "lms_batch"):
		event.lms_batch = batch_name
	for emp in employees[:3]:
		event.append("employees", {"employee": emp})
	event.insert(ignore_permissions=True)


def ensure_lms_course() -> str:
	existing = frappe.db.get_value("LMS Course", {"title": LMS_COURSE_TITLE})
	if existing:
		return existing

	instructor = frappe.db.get_value("User", {"email": DEMO_EMPLOYEES[0]["email"]})
	if not instructor:
		instructor = frappe.session.user
	if "Course Creator" not in frappe.get_roles(instructor):
		frappe.get_doc("User", instructor).add_roles("Course Creator", "Moderator", "LMS Student")

	doc = frappe.get_doc(
		{
			"doctype": "LMS Course",
			"title": LMS_COURSE_TITLE,
			"short_introduction": "Core compliance concepts for MCX operations staff.",
			"description": (
				"<p>Covers the regulatory framework, member obligations, periodic reporting "
				"and KYC hygiene expected across Trading, Clearing and Compliance desks.</p>"
			),
			"published": 1,
			"disable_self_learning": 0,
			"instructors": [{"instructor": instructor}],
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def ensure_lms_batch(course: str) -> str:
	legacy = frappe.db.get_value("LMS Batch", {"title": LEGACY_LMS_BATCH_TITLE})
	if legacy and not frappe.db.exists("LMS Batch", {"title": LMS_BATCH_TITLE}):
		frappe.db.set_value("LMS Batch", legacy, "title", LMS_BATCH_TITLE)

	existing = frappe.db.get_value("LMS Batch", {"title": LMS_BATCH_TITLE})
	if existing:
		return existing

	start = getdate(today())
	instructor = frappe.db.get_value("User", {"email": DEMO_EMPLOYEES[0]["email"]}) or frappe.session.user
	doc = frappe.get_doc(
		{
			"doctype": "LMS Batch",
			"title": LMS_BATCH_TITLE,
			"published": 1,
			"start_date": start,
			"end_date": add_days(start, 30),
			"start_time": "10:00:00",
			"end_time": "12:00:00",
			"timezone": "Asia/Kolkata",
			"description": "Instructor-led compliance cohort for FY 2026-27 onboarding and refreshers.",
			"batch_details": (
				"<p>Cohort covers SEBI / exchange reporting, KYC refresh and desk escalation drills. "
				"Attendance is tracked against the linked Training Event.</p>"
			),
			"allow_self_enrollment": 0,
			"medium": "Online",
			"courses": [{"course": course}],
			"instructors": [{"instructor": instructor}],
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name
