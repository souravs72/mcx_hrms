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
	},
]

LMS_COURSE_TITLE = "MCX Compliance Fundamentals"
LMS_BATCH_TITLE = "MCX Compliance Batch 2026"
TRAINING_PROGRAM_NAME = "MCX Compliance Training Program"
TRAINING_EVENT_NAME = "MCX Compliance Workshop Q1 2026"

JOB_OPENING_TITLE = "Trading Executive - MCX Demo"
JOB_APPLICANT_NAME = "Demo Applicant - Arjun Desai"

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
