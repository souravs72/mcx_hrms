# Copyright (c) 2026, Ascra Technologies LLP and contributors
# For license information, please see license.txt

"""Idempotent demo transactions for client walkthroughs.

Uses native HRMS / ERPNext DocTypes and helpers (Leave Application, Expense Claim,
Employee Checkin, Attendance, Salary Slip, Appraisal, Interview, Job Offer,
Employee Separation) — no custom transaction engines.
"""

from __future__ import annotations

import frappe
from frappe.model.workflow import apply_workflow
from frappe.utils import add_days, get_first_day, get_last_day, getdate, today

from mcx_hrms.constants import (
	COMPANY_NAME,
	DEMO_EMPLOYEES,
	HOLIDAY_LIST_NAME,
	JOB_APPLICANT_NAME,
	JOB_OPENING_TITLE,
	LEGACY_DEMO_TAG,
	SALARY_STRUCTURE_NAME,
	SEED_LABELS,
	SHIFT_TYPE_NAME,
)
from mcx_hrms.setup.hr_lifecycle import (
	APPRAISAL_CYCLE_NAME,
	SEPARATION_TEMPLATE_NAME,
	ensure_holiday_list_assignment,
)

DEMO_TAG = LEGACY_DEMO_TAG  # kept for legacy lookup during polish
BANK_NAME = "HDFC Bank"
COMPANY_BANK_GL = "HDFC Current Account - MCX"
EXPENSE_PAYABLE_GL = "Expense Claims Payable - MCX"
INTERVIEW_TYPE_NAME = "Technical & Domain — Trading Desk"
SKILL_NAME = "Commodity Trading"
LEGACY_INTERVIEW_TYPE = "MCX Technical Round"


def seed_demo_transactions(company: str | None = None) -> dict:
	"""Seed sample HR transactions for client demos. Safe to re-run."""
	company = company or COMPANY_NAME
	if not frappe.db.exists("Company", company):
		frappe.throw(f"Company {company} not found")

	summary: dict[str, list[str]] = {"created": [], "skipped": [], "errors": []}

	def _run(label: str, fn):
		try:
			result = fn()
			if result:
				summary["created"].append(f"{label}: {result}")
			else:
				summary["skipped"].append(label)
		except Exception as e:
			frappe.log_error(title=f"MCX demo seed: {label}", message=frappe.get_traceback())
			summary["errors"].append(f"{label}: {e}")

	employees = _employee_map(company)
	if not employees:
		summary["errors"].append("No demo employees found — run setup_demo_site first")
		return summary

	_run("Company accounts", lambda: ensure_company_accounts(company))
	_run("Workflows sync", lambda: _sync_workflows())
	_run("Polish legacy labels", lambda: polish_legacy_seed_labels(company, employees))
	_run("HR lifecycle masters", lambda: _ensure_lifecycle(company, list(employees.values())))
	_run("Holiday list assignment", lambda: _ensure_hla(company))
	_run("Submit salary structure assignments", lambda: _submit_ssas(company))
	_run("Org hierarchy", lambda: ensure_org_hierarchy(employees))
	_run("Employee bank details", lambda: ensure_employee_bank_details(employees))
	_run("Repair expense claims", lambda: _repair_expense_claim_status())
	_run("Link checkins to attendance", lambda: _link_orphan_checkins())
	_run("Leave applications", lambda: ensure_leave_applications(company, employees))
	_run("Expense claims", lambda: ensure_expense_claims(company, employees))
	_run("Employee advance", lambda: ensure_employee_advance(company, employees))
	_run("Attendance & checkins", lambda: ensure_attendance_and_checkins(company, employees))
	_run("Attendance request", lambda: ensure_attendance_request(company, employees))
	_run("Salary slips", lambda: ensure_salary_slips(company, employees))
	_run("Payroll entry draft", lambda: ensure_payroll_entry_draft(company, employees))
	_run("Appraisal", lambda: ensure_appraisal(company, employees))
	_run("Interview & job offer", lambda: ensure_interview_and_offer(company, employees))
	_run("Employee separation", lambda: ensure_employee_separation(company, employees))
	_run("AI recommendations", lambda: ensure_ai_recommendations())

	frappe.db.commit()
	return summary


def print_seed_transactions_report(company: str | None = None):
	"""bench execute entrypoint."""
	report = seed_demo_transactions(company)
	print("\nMCX HRMS Demo Transactions\n")
	for key in ("created", "skipped", "errors"):
		rows = report.get(key) or []
		print(f"  {key.upper()} ({len(rows)})")
		for row in rows:
			print(f"    - {row}")
	print()
	return report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _employee_map(company: str) -> dict[str, str]:
	"""Map first_name -> Employee name for demo users."""
	out: dict[str, str] = {}
	for spec in DEMO_EMPLOYEES:
		name = frappe.db.get_value("Employee", {"user_id": spec["email"], "company": company})
		if name:
			out[spec["first_name"]] = name
	return out


def _hr_user() -> str:
	return DEMO_EMPLOYEES[0]["email"]


def _already(doctype: str, filters: dict) -> bool:
	return bool(frappe.db.exists(doctype, filters))


def _ensure_hla(company: str) -> str | None:
	before = frappe.db.count("Holiday List Assignment", {"assigned_to": company, "docstatus": 1})
	ensure_holiday_list_assignment(company)
	after = frappe.db.count("Holiday List Assignment", {"assigned_to": company, "docstatus": 1})
	if after > before:
		return "created"
	return None


def _as_user(user: str):
	"""Switch session user; return previous user for restore."""
	prev = frappe.session.user
	frappe.set_user(user)
	return prev


def _sync_workflows() -> str | None:
	from mcx_hrms.setup.workflows import ensure_workflows

	ensure_workflows()
	return "synced"


def _ensure_lifecycle(company: str, employee_ids: list[str]) -> str | None:
	"""Submit leave policy / shift assignments / SSA using native HRMS paths."""
	from mcx_hrms.setup.hr_lifecycle import ensure_hr_lifecycle_demo

	ensure_hr_lifecycle_demo(company, employee_ids)
	return "ok"


def _repair_expense_claim_status() -> str | None:
	"""Fix claims submitted with wrong workflow update_field (status instead of approval_status)."""
	fixed = []
	for name in frappe.get_all(
		"Expense Claim",
		filters={"docstatus": 1, "approval_status": "Draft", "workflow_state": "Approved"},
		pluck="name",
	):
		doc = frappe.get_doc("Expense Claim", name)
		doc.db_set("approval_status", "Approved", update_modified=False)
		doc.reload()
		if hasattr(doc, "set_status"):
			doc.set_status(update=True)
		fixed.append(name)
	return ", ".join(fixed) if fixed else None


def _link_orphan_checkins() -> str | None:
	"""Link seed checkins to same-day Attendance (native attendance field on Employee Checkin)."""
	linked = 0
	device_ids = {
		DEMO_TAG,
		SEED_LABELS["device_mumbai"],
		SEED_LABELS["device_delhi"],
		SEED_LABELS["device_chennai"],
	}
	for ck in frappe.get_all(
		"Employee Checkin",
		filters={"device_id": ["in", list(device_ids)], "attendance": ["in", ["", None]]},
		fields=["name", "employee", "time"],
	):
		day = getdate(ck.time)
		att = frappe.db.get_value(
			"Attendance",
			{"employee": ck.employee, "attendance_date": day, "docstatus": 1},
		)
		if not att:
			continue
		frappe.db.set_value("Employee Checkin", ck.name, "attendance", att, update_modified=False)
		linked += 1
	return f"linked {linked}" if linked else None


def polish_legacy_seed_labels(company: str, employees: dict[str, str]) -> str | None:
	"""Rewrite older 'MCX Demo …' labels to production-looking copy."""
	updated = 0

	def _rename(doctype: str, field: str, old: str, new: str, extra: dict | None = None):
		nonlocal updated
		filters = {field: old}
		if extra:
			filters.update(extra)
		for name in frappe.get_all(doctype, filters=filters, pluck="name"):
			frappe.db.set_value(doctype, name, field, new, update_modified=False)
			updated += 1

	rahul, anita, vikram, meera = (
		employees.get("Rahul"),
		employees.get("Anita"),
		employees.get("Vikram"),
		employees.get("Meera"),
	)
	if rahul:
		_rename("Leave Application", "description", f"{DEMO_TAG} pending leave", SEED_LABELS["leave_pending"], {"employee": rahul})
		_rename("Expense Claim", "remark", f"{DEMO_TAG} approved expense", SEED_LABELS["expense_approved"], {"employee": rahul})
	if anita:
		_rename("Leave Application", "description", f"{DEMO_TAG} approved leave", SEED_LABELS["leave_approved"], {"employee": anita})
	if vikram:
		_rename("Expense Claim", "remark", f"{DEMO_TAG} pending expense L1", SEED_LABELS["expense_pending"], {"employee": vikram})
		_rename("Employee Advance", "purpose", f"{DEMO_TAG} travel imprest", SEED_LABELS["advance"], {"employee": vikram})
	if meera:
		_rename(
			"Attendance Request",
			"explanation",
			f"{DEMO_TAG} WFH regularization",
			SEED_LABELS["attendance_wfh"],
			{"employee": meera},
		)

	for name in frappe.get_all("Employee Checkin", filters={"device_id": DEMO_TAG}, pluck="name"):
		frappe.db.set_value("Employee Checkin", name, "device_id", SEED_LABELS["device_mumbai"], update_modified=False)
		updated += 1

	if frappe.db.exists("Interview Type", LEGACY_INTERVIEW_TYPE) and not frappe.db.exists(
		"Interview Type", INTERVIEW_TYPE_NAME
	):
		frappe.rename_doc("Interview Type", LEGACY_INTERVIEW_TYPE, INTERVIEW_TYPE_NAME, force=True)
		updated += 1

	return f"updated {updated}" if updated else None


def _submit_ssas(company: str) -> str | None:
	"""Ensure Salary Structure + Assignments are submitted from FY start."""
	from mcx_hrms.constants import SALARY_STRUCTURE_NAME

	submitted = []
	structure_submitted = False
	if frappe.db.exists("Salary Structure", SALARY_STRUCTURE_NAME):
		ss = frappe.get_doc("Salary Structure", SALARY_STRUCTURE_NAME)
		if ss.docstatus == 0:
			ss.submit()
			structure_submitted = True

	fy_start = frappe.db.get_value(
		"Fiscal Year",
		{"disabled": 0},
		"year_start_date",
		order_by="year_start_date desc",
	)
	from_date = getdate(fy_start) if fy_start else getdate(f"{getdate(today()).year}-04-01")

	for name in frappe.get_all(
		"Salary Structure Assignment",
		filters={"company": company, "docstatus": 0},
		pluck="name",
	):
		doc = frappe.get_doc("Salary Structure Assignment", name)
		if getdate(doc.from_date) != from_date:
			doc.from_date = from_date
			doc.save(ignore_permissions=True)
		doc.submit()
		submitted.append(name)

	if not structure_submitted and not submitted:
		return None
	parts = []
	if structure_submitted:
		parts.append("salary structure")
	if submitted:
		parts.append(f"{len(submitted)} SSA")
	return ", ".join(parts)


# ---------------------------------------------------------------------------
# Company / org / bank
# ---------------------------------------------------------------------------


def ensure_company_accounts(company: str) -> str | None:
	"""Ensure payable, bank GL, and expense-claim type accounts used by native HR docs."""
	created = []

	# Expense Claims Payable (Liability)
	if not frappe.db.exists("Account", EXPENSE_PAYABLE_GL):
		parent = frappe.db.get_value(
			"Account", {"company": company, "account_name": "Accounts Payable", "is_group": 1}
		)
		if parent:
			frappe.get_doc(
				{
					"doctype": "Account",
					"account_name": "Expense Claims Payable",
					"parent_account": parent,
					"company": company,
					"account_type": "Payable",
					"is_group": 0,
				}
			).insert(ignore_permissions=True)
			created.append(EXPENSE_PAYABLE_GL)

	frappe.db.set_value(
		"Company",
		company,
		"default_expense_claim_payable_account",
		EXPENSE_PAYABLE_GL if frappe.db.exists("Account", EXPENSE_PAYABLE_GL) else "Creditors - MCX",
	)

	# Company bank GL
	if not frappe.db.exists("Account", COMPANY_BANK_GL):
		parent = frappe.db.get_value(
			"Account", {"company": company, "account_name": "Bank Accounts", "is_group": 1}
		)
		if parent:
			frappe.get_doc(
				{
					"doctype": "Account",
					"account_name": "HDFC Current Account",
					"parent_account": parent,
					"company": company,
					"account_type": "Bank",
					"is_group": 0,
				}
			).insert(ignore_permissions=True)
			created.append(COMPANY_BANK_GL)

	if frappe.db.exists("Account", COMPANY_BANK_GL):
		frappe.db.set_value("Company", company, "default_bank_account", COMPANY_BANK_GL)

	# Bank master
	if not frappe.db.exists("Bank", BANK_NAME):
		frappe.get_doc({"doctype": "Bank", "bank_name": BANK_NAME}).insert(ignore_permissions=True)
		created.append(BANK_NAME)

	# Map expense claim types → Travel Expenses account
	expense_account = "Travel Expenses - MCX"
	if not frappe.db.exists("Account", expense_account):
		expense_account = "Administrative Expenses - MCX"
	for claim_type in ("Travel", "Food", "Accommodation", "Communication"):
		if not frappe.db.exists("Expense Claim Type", claim_type):
			continue
		doc = frappe.get_doc("Expense Claim Type", claim_type)
		if any(row.company == company for row in doc.accounts):
			continue
		doc.append("accounts", {"company": company, "default_account": expense_account})
		doc.save(ignore_permissions=True)
		created.append(f"{claim_type} account map")

	# Employee Advance must use a Receivable account (native HRMS validation)
	advance_recv = "Employee Advance Receivable - MCX"
	if not frappe.db.exists("Account", advance_recv):
		parent = frappe.db.get_value(
			"Account", {"company": company, "account_name": "Current Assets", "is_group": 1}
		) or frappe.db.get_value(
			"Account", {"company": company, "account_name": "Accounts Receivable", "is_group": 1}
		)
		if parent:
			frappe.get_doc(
				{
					"doctype": "Account",
					"account_name": "Employee Advance Receivable",
					"parent_account": parent,
					"company": company,
					"account_type": "Receivable",
					"is_group": 0,
				}
			).insert(ignore_permissions=True)
			created.append(advance_recv)

	if frappe.db.exists("Account", advance_recv):
		frappe.db.set_value("Company", company, "default_employee_advance_account", advance_recv)

	return ", ".join(created) if created else None


def ensure_org_hierarchy(employees: dict[str, str]) -> str | None:
	"""Set reports_to + leave/expense approver using native Employee fields."""
	hr = employees.get("Priya")
	if not hr:
		return None

	hr_user = _hr_user()
	updated = []
	for first_name, emp in employees.items():
		doc = frappe.get_doc("Employee", emp)
		changed = False
		if first_name != "Priya" and doc.reports_to != hr:
			doc.reports_to = hr
			changed = True
		if doc.leave_approver != hr_user:
			doc.leave_approver = hr_user
			changed = True
		if doc.expense_approver != hr_user:
			doc.expense_approver = hr_user
			changed = True
		if not doc.holiday_list and frappe.db.exists("Holiday List", HOLIDAY_LIST_NAME):
			doc.holiday_list = HOLIDAY_LIST_NAME
			changed = True
		if changed:
			doc.save(ignore_permissions=True)
			updated.append(emp)
	return f"updated {len(updated)}" if updated else None


def ensure_employee_bank_details(employees: dict[str, str]) -> str | None:
	"""Populate Employee salary_mode / bank fields + ERPNext Bank Account party link."""
	if not frappe.db.exists("Bank", BANK_NAME):
		return None

	spec_by_first = {s["first_name"]: s for s in DEMO_EMPLOYEES}
	created = []
	for first_name, emp in employees.items():
		spec = spec_by_first.get(first_name) or {}
		doc = frappe.get_doc("Employee", emp)
		ac_no = spec.get("bank_ac_no") or f"50100{abs(hash(emp)) % 1000000:06d}"
		changed = False
		if doc.salary_mode != "Bank":
			doc.salary_mode = "Bank"
			changed = True
		if doc.bank_name != BANK_NAME:
			doc.bank_name = BANK_NAME
			changed = True
		if doc.bank_ac_no != ac_no:
			doc.bank_ac_no = ac_no
			changed = True
		if spec.get("ifsc") and hasattr(doc, "ifsc_code") and doc.ifsc_code != spec["ifsc"]:
			doc.ifsc_code = spec["ifsc"]
			changed = True
		if changed:
			doc.save(ignore_permissions=True)

		existing = frappe.db.exists(
			"Bank Account", {"party_type": "Employee", "party": emp, "bank": BANK_NAME}
		)
		if existing:
			continue

		frappe.get_doc(
			{
				"doctype": "Bank Account",
				"account_name": f"{doc.employee_name} — Salary",
				"bank": BANK_NAME,
				"party_type": "Employee",
				"party": emp,
				"bank_account_no": ac_no,
				"is_default": 1,
				"is_company_account": 0,
			}
		).insert(ignore_permissions=True)
		created.append(emp)

	# Company bank account (for Payroll Entry payment_account story)
	if frappe.db.exists("Account", COMPANY_BANK_GL) and not frappe.db.exists(
		"Bank Account", {"account_name": "MCX HDFC Salary Disbursement", "is_company_account": 1}
	):
		frappe.get_doc(
			{
				"doctype": "Bank Account",
				"account_name": "MCX HDFC Salary Disbursement",
				"bank": BANK_NAME,
				"is_company_account": 1,
				"company": COMPANY_NAME,
				"account": COMPANY_BANK_GL,
				"bank_account_no": "502000112233",
				"is_default": 1,
			}
		).insert(ignore_permissions=True)
		created.append("company bank")

	return f"created {len(created)}" if created else None


# ---------------------------------------------------------------------------
# Leave
# ---------------------------------------------------------------------------


def ensure_leave_applications(company: str, employees: dict[str, str]) -> str | None:
	"""Create pending + approved leave via native Leave Application + Workflow."""
	rahul = employees.get("Rahul")
	anita = employees.get("Anita")
	if not rahul:
		return None

	created = []
	approver = _hr_user()

	# Pending — for live MSS approval
	if not _already(
		"Leave Application",
		{"employee": rahul, "description": SEED_LABELS["leave_pending"]},
	) and not _already(
		"Leave Application",
		{"employee": rahul, "description": f"{DEMO_TAG} pending leave"},
	):
		from_date = _leave_date_within_allocation(rahul, "Casual Leave", prefer_future=True)
		la = frappe.get_doc(
			{
				"doctype": "Leave Application",
				"employee": rahul,
				"leave_type": "Casual Leave",
				"from_date": from_date,
				"to_date": from_date,
				"company": company,
				"status": "Open",
				"leave_approver": approver,
				"description": SEED_LABELS["leave_pending"],
			}
		)
		la.insert(ignore_permissions=True)
		apply_workflow(la, "Submit for Approval")
		created.append(la.name)

	# Approved — historical
	if anita and not _already(
		"Leave Application",
		{"employee": anita, "description": SEED_LABELS["leave_approved"]},
	) and not _already(
		"Leave Application",
		{"employee": anita, "description": f"{DEMO_TAG} approved leave"},
	):
		from_date = _leave_date_within_allocation(anita, "Casual Leave", prefer_future=False)
		la = frappe.get_doc(
			{
				"doctype": "Leave Application",
				"employee": anita,
				"leave_type": "Casual Leave",
				"from_date": from_date,
				"to_date": from_date,
				"company": company,
				"status": "Open",
				"leave_approver": approver,
				"description": SEED_LABELS["leave_approved"],
			}
		)
		la.insert(ignore_permissions=True)
		apply_workflow(la, "Submit for Approval")
		la.reload()
		prev = _as_user(approver)
		try:
			apply_workflow(la, "Approve")
		finally:
			frappe.set_user(prev)
		created.append(la.name)

	return ", ".join(created) if created else None


def _leave_date_within_allocation(employee: str, leave_type: str, prefer_future: bool):
	"""Pick a leave date inside an existing allocation, creating one if needed."""
	year = getdate(today()).year
	alloc = frappe.db.get_value(
		"Leave Allocation",
		{"employee": employee, "leave_type": leave_type, "docstatus": 1},
		["from_date", "to_date"],
		as_dict=True,
		order_by="to_date desc",
	)
	if not alloc:
		# Fallback allocation for demo when LPA did not create one (e.g. rehomed employees)
		alloc_doc = frappe.get_doc(
			{
				"doctype": "Leave Allocation",
				"employee": employee,
				"leave_type": leave_type,
				"from_date": f"{year}-01-01",
				"to_date": f"{year}-12-31",
				"new_leaves_allocated": 12,
			}
		)
		alloc_doc.insert(ignore_permissions=True)
		alloc_doc.submit()
		alloc = frappe._dict(from_date=alloc_doc.from_date, to_date=alloc_doc.to_date)

	start, end = getdate(alloc.from_date), getdate(alloc.to_date)
	if prefer_future:
		candidate = add_days(getdate(today()), 5)
		if candidate < start:
			candidate = start
		if candidate > end:
			candidate = end
		return candidate

	candidate = add_days(getdate(today()), -10)
	if candidate < start:
		candidate = start
	if candidate > end:
		candidate = end
	return candidate


# ---------------------------------------------------------------------------
# Expense / Advance
# ---------------------------------------------------------------------------


def ensure_expense_claims(company: str, employees: dict[str, str]) -> str | None:
	"""Draft-at-L1 claim for live approval + fully approved claim for history."""
	vikram = employees.get("Vikram")
	rahul = employees.get("Rahul")
	if not vikram:
		return None

	payable = frappe.db.get_value("Company", company, "default_expense_claim_payable_account")
	cost_center = frappe.db.get_value("Company", company, "cost_center")
	currency = frappe.db.get_value("Company", company, "default_currency") or "INR"
	approver = _hr_user()
	created = []

	def _make_claim(employee: str, amount: float, remark: str, advance_workflow: bool) -> str | None:
		if _already("Expense Claim", {"employee": employee, "remark": remark}):
			return None
		claim = frappe.get_doc(
			{
				"doctype": "Expense Claim",
				"employee": employee,
				"company": company,
				"currency": currency,
				"exchange_rate": 1,
				"payable_account": payable,
				"expense_approver": approver,
				"approval_status": "Draft",
				"remark": remark,
				"expenses": [
					{
						"expense_type": "Travel",
						"expense_date": today(),
						"amount": amount,
						"sanctioned_amount": amount,
						"cost_center": cost_center,
						"description": remark,
					}
				],
			}
		)
		claim.insert(ignore_permissions=True)
		if advance_workflow:
			apply_workflow(claim, "Submit for Approval")
		return claim.name

	# Live approval queue — stop at Pending L1
	name = _make_claim(vikram, 4850, SEED_LABELS["expense_pending"], True)
	if name:
		created.append(name)

	# Fully approved history — workflow updates approval_status on final Approve
	if rahul and not _already(
		"Expense Claim", {"employee": rahul, "remark": SEED_LABELS["expense_approved"]}
	) and not _already("Expense Claim", {"employee": rahul, "remark": f"{DEMO_TAG} approved expense"}):
		name = _make_claim(rahul, 1650, SEED_LABELS["expense_approved"], True)
		if name:
			claim = frappe.get_doc("Expense Claim", name)
			prev = _as_user(approver)
			try:
				for _ in range(4):
					claim.reload()
					apply_workflow(claim, "Approve")
			finally:
				frappe.set_user(prev)
			created.append(name)

	return ", ".join(created) if created else None


def ensure_employee_advance(company: str, employees: dict[str, str]) -> str | None:
	emp = employees.get("Vikram")
	if not emp:
		return None
	purpose = SEED_LABELS["advance"]
	if _already("Employee Advance", {"employee": emp, "purpose": purpose}) or _already(
		"Employee Advance", {"employee": emp, "purpose": f"{DEMO_TAG} travel imprest"}
	):
		return None

	currency = frappe.db.get_value("Company", company, "default_currency") or "INR"
	advance_account = frappe.db.get_value("Company", company, "default_employee_advance_account")
	doc = frappe.get_doc(
		{
			"doctype": "Employee Advance",
			"employee": emp,
			"company": company,
			"purpose": purpose,
			"advance_amount": 7500,
			"posting_date": today(),
			"currency": currency,
			"exchange_rate": 1,
			"advance_account": advance_account,
			"status": "Draft",
		}
	)
	doc.insert(ignore_permissions=True)
	# Keep as draft so walkthrough can show submit + payment without forcing GL
	return doc.name


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------


def ensure_attendance_and_checkins(company: str, employees: dict[str, str]) -> str | None:
	"""Native Employee Checkin (IN/OUT) linked to Attendance via mark_attendance_and_link_log."""
	from hrms.hr.doctype.employee_checkin.employee_checkin import mark_attendance_and_link_log

	created = []
	targets = [
		(employees.get("Rahul"), SEED_LABELS["device_mumbai"], 19.0760, 72.8777),
		(employees.get("Anita"), SEED_LABELS["device_delhi"], 28.6139, 77.2090),
		(employees.get("Vikram"), SEED_LABELS["device_mumbai"], 19.0760, 72.8777),
	]
	targets = [t for t in targets if t[0]]
	if not targets:
		return None

	for days_ago in (5, 4, 3, 2, 1):
		day = add_days(getdate(today()), -days_ago)
		if day.weekday() >= 5:
			continue
		for emp, device_id, lat, lng in targets:
			# Slight stagger so punches look human
			in_minute = 2 + (hash(emp) % 12)
			out_minute = 5 + (hash(emp + "out") % 20)
			in_time = f"{day} 09:{in_minute:02d}:00"
			out_time = f"{day} 18:{out_minute:02d}:00"

			if frappe.db.exists("Attendance", {"employee": emp, "attendance_date": day, "docstatus": 1}):
				continue

			logs = []
			in_name = frappe.db.exists("Employee Checkin", {"employee": emp, "time": in_time})
			if not in_name:
				logs.append(
					frappe.get_doc(
						{
							"doctype": "Employee Checkin",
							"employee": emp,
							"time": in_time,
							"log_type": "IN",
							"device_id": device_id,
							"latitude": lat,
							"longitude": lng,
						}
					).insert(ignore_permissions=True)
				)
			else:
				logs.append(frappe.get_doc("Employee Checkin", in_name))

			out_name = frappe.db.exists("Employee Checkin", {"employee": emp, "time": out_time})
			if not out_name:
				logs.append(
					frappe.get_doc(
						{
							"doctype": "Employee Checkin",
							"employee": emp,
							"time": out_time,
							"log_type": "OUT",
							"device_id": device_id,
							"latitude": lat,
							"longitude": lng,
						}
					).insert(ignore_permissions=True)
				)
			else:
				logs.append(frappe.get_doc("Employee Checkin", out_name))

			from frappe.utils import get_datetime

			att = mark_attendance_and_link_log(
				logs=logs,
				attendance_status="Present",
				attendance_date=day,
				working_hours=9.0,
				in_time=get_datetime(in_time),
				out_time=get_datetime(out_time),
				shift=SHIFT_TYPE_NAME,
			)
			if att:
				created.append(getattr(att, "name", str(att)))

	return f"{len(created)} punches" if created else None


def ensure_attendance_request(company: str, employees: dict[str, str]) -> str | None:
	emp = employees.get("Meera")
	if not emp:
		return None
	# Use a future/recent date without attendance conflict
	from_date = add_days(getdate(today()), -1)
	if _already(
		"Attendance Request",
		{"employee": emp, "from_date": from_date, "reason": "Work From Home"},
	):
		return None

	# Avoid clash with submitted Attendance on same day
	if frappe.db.exists("Attendance", {"employee": emp, "attendance_date": from_date, "docstatus": 1}):
		from_date = add_days(getdate(today()), 1)

	doc = frappe.get_doc(
		{
			"doctype": "Attendance Request",
			"employee": emp,
			"company": company,
			"from_date": from_date,
			"to_date": from_date,
			"reason": "Work From Home",
			"explanation": SEED_LABELS["attendance_wfh"],
		}
	)
	doc.insert(ignore_permissions=True)
	# Leave draft for live submit (submit creates Attendance)
	return doc.name


# ---------------------------------------------------------------------------
# Payroll
# ---------------------------------------------------------------------------


def ensure_salary_slips(company: str, employees: dict[str, str]) -> str | None:
	"""Create submitted salary slips via native make_salary_slip (correct autoname)."""
	make_salary_slip = _get_make_salary_slip()

	if not frappe.db.exists("Salary Structure", SALARY_STRUCTURE_NAME):
		return None

	# Prefer previous month when it falls inside SSA/FY; else use current month
	ref = add_days(get_first_day(today()), -1)
	ssa_from = frappe.db.get_value(
		"Salary Structure Assignment",
		{"company": company, "docstatus": 1},
		"from_date",
		order_by="from_date asc",
	)
	if ssa_from and getdate(ref) < getdate(ssa_from):
		ref = getdate(today())

	start = get_first_day(ref)
	end = get_last_day(ref)
	posting = min(getdate(today()), getdate(end))

	# Repair misnamed slips from earlier seed (Sal Slip/None/…)
	_repair_misnamed_salary_slips(company)

	created = []
	for first_name in ("Priya", "Rahul", "Anita"):
		emp = employees.get(first_name)
		if not emp:
			continue
		if frappe.db.exists(
			"Salary Slip",
			{"employee": emp, "start_date": start, "end_date": end, "docstatus": ["<", 2]},
		):
			continue

		slip = make_salary_slip(
			SALARY_STRUCTURE_NAME,
			employee=emp,
			posting_date=str(posting),
			ignore_permissions=True,
		)
		# SalarySlip.__init__ bakes employee into default_series before postprocess sets it
		slip.employee = emp
		slip.default_series = f"Sal Slip/{emp}/.#####"
		slip.start_date = start
		slip.end_date = end
		slip.posting_date = posting
		slip.company = company
		slip.flags.ignore_permissions = True
		if hasattr(slip, "process_salary_structure"):
			slip.process_salary_structure()
		slip.insert(ignore_permissions=True)
		slip.submit()
		created.append(slip.name)

	return ", ".join(created) if created else None


def _get_make_salary_slip():
	"""HRMS versions differ: older exposes make_salary_slip only; newer also has _make_salary_slip."""
	from hrms.payroll.doctype.salary_structure import salary_structure as ss_mod

	if hasattr(ss_mod, "_make_salary_slip"):
		return ss_mod._make_salary_slip
	return ss_mod.make_salary_slip


def _repair_misnamed_salary_slips(company: str):
	"""Cancel submitted slips whose name still contains /None/ from broken autoname."""
	for name in frappe.get_all(
		"Salary Slip",
		filters={"company": company, "name": ["like", "Sal Slip/None/%"], "docstatus": 1},
		pluck="name",
	):
		try:
			frappe.get_doc("Salary Slip", name).cancel()
		except Exception:
			frappe.log_error(title="MCX demo cancel misnamed slip", message=frappe.get_traceback())


def ensure_payroll_entry_draft(company: str, employees: dict[str, str]) -> str | None:
	"""Draft Payroll Entry for current month — live demo of create salary slips."""
	start = get_first_day(today())
	end = get_last_day(today())
	if _already("Payroll Entry", {"company": company, "start_date": start, "end_date": end}):
		return None

	currency = frappe.db.get_value("Company", company, "default_currency") or "INR"
	cost_center = frappe.db.get_value("Company", company, "cost_center")
	payable = frappe.db.get_value("Company", company, "default_payroll_payable_account")
	payment = frappe.db.get_value("Company", company, "default_bank_account") or frappe.db.get_value(
		"Company", company, "default_cash_account"
	)

	pe = frappe.new_doc("Payroll Entry")
	pe.company = company
	pe.currency = currency
	pe.exchange_rate = 1
	pe.payroll_frequency = "Monthly"
	pe.start_date = start
	pe.end_date = end
	pe.posting_date = end
	pe.cost_center = cost_center
	pe.payroll_payable_account = payable
	pe.payment_account = payment
	pe.fill_employee_details()
	pe.insert(ignore_permissions=True)
	return pe.name


# ---------------------------------------------------------------------------
# PMS / Recruitment / Exit
# ---------------------------------------------------------------------------


def ensure_appraisal(company: str, employees: dict[str, str]) -> str | None:
	emp = employees.get("Rahul")
	if not emp or not frappe.db.exists("Appraisal Cycle", APPRAISAL_CYCLE_NAME):
		return None
	if _already("Appraisal", {"employee": emp, "appraisal_cycle": APPRAISAL_CYCLE_NAME}):
		return None

	template = frappe.db.get_value("Appraisal Template", {"template_title": "MCX Annual Appraisal Template"})
	app = frappe.get_doc(
		{
			"doctype": "Appraisal",
			"employee": emp,
			"company": company,
			"appraisal_cycle": APPRAISAL_CYCLE_NAME,
			"appraisal_template": template,
		}
	)
	if hasattr(app, "set_kras_and_rating_criteria"):
		app.set_kras_and_rating_criteria()
	app.insert(ignore_permissions=True)
	return app.name


def ensure_interview_and_offer(company: str, employees: dict[str, str]) -> str | None:
	from mcx_hrms.constants import LEGACY_JOB_APPLICANT_NAME

	applicant = frappe.db.get_value("Job Applicant", {"applicant_name": JOB_APPLICANT_NAME})
	if not applicant:
		applicant = frappe.db.get_value("Job Applicant", {"applicant_name": LEGACY_JOB_APPLICANT_NAME})
	if not applicant:
		return None

	created = []

	if not frappe.db.exists("Skill", SKILL_NAME):
		skill = frappe.get_doc({"doctype": "Skill", "skill_name": SKILL_NAME})
		skill.insert(ignore_permissions=True)

	if not frappe.db.exists("Interview Type", INTERVIEW_TYPE_NAME):
		itype = frappe.get_doc(
			{
				"doctype": "Interview Type",
				"interview_type_name": INTERVIEW_TYPE_NAME,
				"description": SEED_LABELS["interview_type"],
				"expected_average_rating": 3.5,
				"expected_skill_set": [{"skill": SKILL_NAME}],
			}
		)
		itype.insert(ignore_permissions=True)

	# Link applicant to job opening (native Job Applicant.job_title → Job Opening)
	opening = frappe.db.get_value("Job Opening", {"job_title": JOB_OPENING_TITLE})
	if opening and not frappe.db.get_value("Job Applicant", applicant, "job_title"):
		frappe.db.set_value("Job Applicant", applicant, "job_title", opening)

	interviewer = _hr_user()
	if not _already("Interview", {"job_applicant": applicant, "interview_type": INTERVIEW_TYPE_NAME}):
		scheduled = add_days(getdate(today()), 2)
		interview = frappe.get_doc(
			{
				"doctype": "Interview",
				"interview_type": INTERVIEW_TYPE_NAME,
				"job_applicant": applicant,
				"job_opening": opening,
				"scheduled_on": scheduled,
				"from_time": "11:00:00",
				"to_time": "12:00:00",
				"status": "Pending",
				"interview_details": [{"interviewer": interviewer}],
			}
		)
		interview.insert(ignore_permissions=True)
		created.append(interview.name)

	if not _already("Job Offer", {"job_applicant": applicant}):
		from frappe.model.naming import make_autoname

		offer = frappe.get_doc(
			{
				"doctype": "Job Offer",
				"job_applicant": applicant,
				"applicant_name": JOB_APPLICANT_NAME,
				"offer_date": today(),
				"designation": "Trading Executive",
				"company": company,
				"status": "Awaiting Response",
			}
		)
		# Some HRMS/site setups fail expression autoname ("Please set the document name")
		try:
			offer.name = make_autoname("HR-OFF-.YYYY.-.#####")
			offer.flags.name_set = True
		except Exception:
			pass
		offer.insert(ignore_permissions=True)
		# Keep draft/submitted lightly — submit if no vacancy check issues
		try:
			offer.submit()
		except Exception:
			frappe.log_error(title="MCX demo Job Offer submit", message=frappe.get_traceback())
		created.append(offer.name)

	return ", ".join(created) if created else None


def ensure_employee_separation(company: str, employees: dict[str, str]) -> str | None:
	"""Separation checklist for demo — uses Meera (does not resign for real)."""
	emp = employees.get("Meera")
	if not emp:
		return None
	if _already("Employee Separation", {"employee": emp}):
		return None

	template = frappe.db.get_value(
		"Employee Separation Template", {"title": SEPARATION_TEMPLATE_NAME}
	)
	doc = frappe.get_doc(
		{
			"doctype": "Employee Separation",
			"employee": emp,
			"company": company,
			"boarding_begins_on": today(),
			"boarding_status": "Pending",
			"employee_separation_template": template,
			"activities": [
				{
					"activity_name": "Return company assets",
					"description": SEED_LABELS["separation_assets"],
				},
				{
					"activity_name": "Revoke system access",
					"description": SEED_LABELS["separation_access"],
				},
				{
					"activity_name": "Full and Final settlement",
					"description": SEED_LABELS["separation_fnf"],
				},
			],
		}
	)
	doc.insert(ignore_permissions=True)
	# Keep draft so walkthrough can show submit → project/tasks creation
	return doc.name


def ensure_ai_recommendations() -> str | None:
	"""Warm MCX Learning AI recommendations so /ai-learning is not empty."""
	if "mcx_learning_ai" not in frappe.get_installed_apps():
		return None

	from mcx_learning_ai.recommendations import generate_recommendations

	user = DEMO_EMPLOYEES[1]["email"]  # Rahul — LMS learner persona
	if not frappe.db.exists("User", user):
		return None

	# Administrator is System Manager — may generate for another user
	recs = generate_recommendations(user=user, limit=10)
	count = len(recs) if isinstance(recs, list) else 0
	return f"{count} for {user}" if count else None
