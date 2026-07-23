# Copyright (c) 2026, Ascra Technologies LLP and contributors
# For license information, please see license.txt

"""Shared constants for MCX HRMS demo and setup."""

from __future__ import annotations

COMPANY_NAME = "MCX"
COMPANY_ABBR = "MCX"
DEMO_SITE = "mcx.site"

BRANCHES = ["Mumbai HQ", "Delhi Regional", "Chennai Operations"]

DEPARTMENTS = [
	"Human Resources",
	"Trading Operations",
	"Clearing & Settlement",
	"Information Technology",
	"Compliance",
]

DESIGNATIONS = [
	"HR Manager",
	"Trading Executive",
	"Clearing Officer",
	"Software Engineer",
	"Compliance Analyst",
	"HR Executive",
]

EMPLOYEE_GRADES = ["Grade A", "Grade B", "Grade C"]

LEAVE_TYPES = [
	{"name": "Casual Leave", "max_leaves_allowed": 12, "is_carry_forward": 0},
	{"name": "Sick Leave", "max_leaves_allowed": 10, "is_carry_forward": 0},
	{"name": "Earned Leave", "max_leaves_allowed": 15, "is_carry_forward": 1},
]

EXPENSE_CLAIM_TYPES = [
	"Travel",
	"Food",
	"Accommodation",
	"Communication",
]

SALARY_COMPONENTS = [
	{"name": "Basic", "type": "Earning", "salary_component_abbr": "BASIC"},
	{"name": "House Rent Allowance", "type": "Earning", "salary_component_abbr": "HRA"},
	{"name": "Special Allowance", "type": "Earning", "salary_component_abbr": "SA"},
	{"name": "Provident Fund", "type": "Deduction", "salary_component_abbr": "PF"},
]

# Password for all seeded ESS/MSS users (share only in demo briefings)
DEMO_USER_PASSWORD = "demo@123"

DEMO_EMPLOYEES = [
	{
		"email": "priya.sharma@mcx.demo",
		"first_name": "Priya",
		"last_name": "Sharma",
		"department": "Human Resources",
		"designation": "HR Manager",
		"grade": "Grade A",
		"branch": "Mumbai HQ",
		"gender": "Female",
		"date_of_birth": "1986-03-12",
		"date_of_joining": "2015-06-01",
		"cell_number": "9820012345",
		"permanent_address": "14, Bandra Kurla Complex, Mumbai 400051",
		"current_address": "14, Bandra Kurla Complex, Mumbai 400051",
		"bank_ac_no": "501001112233",
		"ifsc": "HDFC0000240",
	},
	{
		"email": "rahul.mehta@mcx.demo",
		"first_name": "Rahul",
		"last_name": "Mehta",
		"department": "Trading Operations",
		"designation": "Trading Executive",
		"grade": "Grade B",
		"branch": "Mumbai HQ",
		"gender": "Male",
		"date_of_birth": "1992-08-21",
		"date_of_joining": "2019-04-15",
		"cell_number": "9876543210",
		"permanent_address": "302, Powai Heights, Mumbai 400076",
		"current_address": "302, Powai Heights, Mumbai 400076",
		"bank_ac_no": "501001112244",
		"ifsc": "HDFC0000240",
	},
	{
		"email": "anita.patel@mcx.demo",
		"first_name": "Anita",
		"last_name": "Patel",
		"department": "Clearing & Settlement",
		"designation": "Clearing Officer",
		"grade": "Grade B",
		"branch": "Delhi Regional",
		"gender": "Female",
		"date_of_birth": "1990-11-05",
		"date_of_joining": "2018-09-03",
		"cell_number": "9811122233",
		"permanent_address": "B-22, Connaught Place, New Delhi 110001",
		"current_address": "B-22, Connaught Place, New Delhi 110001",
		"bank_ac_no": "501001112255",
		"ifsc": "HDFC0001234",
	},
	{
		"email": "vikram.singh@mcx.demo",
		"first_name": "Vikram",
		"last_name": "Singh",
		"department": "Information Technology",
		"designation": "Software Engineer",
		"grade": "Grade B",
		"branch": "Mumbai HQ",
		"gender": "Male",
		"date_of_birth": "1994-01-30",
		"date_of_joining": "2021-01-11",
		"cell_number": "9900011122",
		"permanent_address": "701, Andheri East, Mumbai 400069",
		"current_address": "701, Andheri East, Mumbai 400069",
		"bank_ac_no": "501001112266",
		"ifsc": "HDFC0000240",
	},
	{
		"email": "meera.iyer@mcx.demo",
		"first_name": "Meera",
		"last_name": "Iyer",
		"department": "Compliance",
		"designation": "Compliance Analyst",
		"grade": "Grade C",
		"branch": "Chennai Operations",
		"gender": "Female",
		"date_of_birth": "1996-07-18",
		"date_of_joining": "2022-08-01",
		"cell_number": "9444012345",
		"permanent_address": "12, T Nagar, Chennai 600017",
		"current_address": "12, T Nagar, Chennai 600017",
		"bank_ac_no": "501001112277",
		"ifsc": "HDFC0005678",
	},
]

LMS_COURSE_TITLE = "MCX Compliance Fundamentals"
LMS_BATCH_TITLE = "MCX Compliance Batch FY 2026-27"
TRAINING_PROGRAM_NAME = "MCX Compliance Training Program"
TRAINING_EVENT_NAME = "SEBI Compliance Refresher — Q1 FY 2026-27"

JOB_OPENING_TITLE = "Trading Executive — Equity & Commodity Desk"
JOB_APPLICANT_NAME = "Arjun Desai"
JOB_APPLICANT_EMAIL = "arjun.desai@outlook.com"

# Legacy labels (pre-polish) — used to rename existing seed rows
LEGACY_JOB_OPENING_TITLE = "Trading Executive - MCX Demo"
LEGACY_JOB_APPLICANT_NAME = "Demo Applicant - Arjun Desai"
LEGACY_TRAINING_EVENT_NAME = "MCX Compliance Workshop Q1 2026"
LEGACY_LMS_BATCH_TITLE = "MCX Compliance Batch 2026"

HOLIDAY_LIST_NAME = "MCX Holiday List 2026"
LEAVE_POLICY_TITLE = "MCX Standard Leave Policy"
SHIFT_TYPE_NAME = "MCX General Shift"
SALARY_STRUCTURE_NAME = "MCX Standard Salary Structure"

EXPENSE_APPROVAL_ROLES = [
	"MCX Expense Approver L1",
	"MCX Expense Approver L2",
	"MCX Expense Approver L3",
	"MCX Expense Approver L4",
]

# Production-looking seed keys (also used for idempotency)
SEED_LABELS = {
	"leave_pending": "Family function — Casual Leave",
	"leave_approved": "Medical appointment — Casual Leave",
	"expense_pending": "Ahmedabad member onboarding — travel",
	"expense_approved": "Client meeting — local conveyance",
	"advance": "Member visit imprest — Ahmedabad",
	"attendance_wfh": "Work from home — settlement window support",
	"device_mumbai": "MCX-MUM-BIO-01",
	"device_delhi": "MCX-DEL-BIO-01",
	"device_chennai": "MCX-CHN-BIO-01",
	"interview_type": "Technical & domain interview — Trading Desk",
	"separation_assets": "Collect laptop, access card and market data tokens",
	"separation_access": "Revoke Desk, LMS, VPN and mailbox access",
	"separation_fnf": "Complete full & final settlement and Form 16 handoff",
}
LEGACY_DEMO_TAG = "MCX Demo"
