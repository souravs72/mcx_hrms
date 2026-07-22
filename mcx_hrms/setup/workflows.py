# Copyright (c) 2026, Ascra Technologies LLP and contributors
# For license information, please see license.txt

"""Workflow definitions for MCX HRMS demo."""

from __future__ import annotations

import frappe

from mcx_hrms.constants import EXPENSE_APPROVAL_ROLES


def ensure_workflows():
	_ensure_expense_approval_roles()
	ensure_job_requisition_workflow()
	ensure_expense_claim_workflow()
	ensure_leave_application_workflow()


def _ensure_expense_approval_roles():
	for role in EXPENSE_APPROVAL_ROLES:
		if frappe.db.exists("Role", role):
			continue
		frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
			ignore_permissions=True
		)


def _ensure_workflow_state(state: str):
	if frappe.db.exists("Workflow State", state):
		return
	frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": state, "style": "Primary"}).insert(
		ignore_permissions=True
	)


def _ensure_workflow_action(action: str):
	if frappe.db.exists("Workflow Action Master", action):
		return
	frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(
		ignore_permissions=True
	)


def _create_workflow_if_missing(workflow_name: str, document_type: str, states: list, transitions: list):
	if frappe.db.exists("Workflow", workflow_name):
		return

	for state in states:
		_ensure_workflow_state(state["state"])

	for transition in transitions:
		_ensure_workflow_action(transition["action"])

	workflow = frappe.new_doc("Workflow")
	workflow.workflow_name = workflow_name
	workflow.document_type = document_type
	workflow.workflow_state_field = "workflow_state"
	workflow.is_active = 1
	workflow.send_email_alert = 0
	workflow.override_status = 0

	for state in states:
		workflow.append("states", state)

	for transition in transitions:
		workflow.append("transitions", transition)

	workflow.insert(ignore_permissions=True)


def _create_or_sync_workflow(workflow_name: str, document_type: str, states: list, transitions: list):
	"""Create workflow, or sync state update_field/update_value on an existing one."""
	if not frappe.db.exists("Workflow", workflow_name):
		_create_workflow_if_missing(workflow_name, document_type, states, transitions)
		return

	workflow = frappe.get_doc("Workflow", workflow_name)
	desired = {s["state"]: s for s in states}
	changed = False
	for row in workflow.states:
		spec = desired.get(row.state)
		if not spec:
			continue
		for key in ("update_field", "update_value", "doc_status", "allow_edit"):
			if key in spec and row.get(key) != spec[key]:
				row.set(key, spec[key])
				changed = True
	if changed:
		workflow.save(ignore_permissions=True)


def ensure_job_requisition_workflow():
	workflow_name = "MCX Job Requisition Approval"
	states = [
		{"state": "Pending", "doc_status": "0", "allow_edit": "HR User"},
		{"state": "Manager Review", "doc_status": "0", "allow_edit": "HR Manager"},
		{
			"state": "Approved",
			"doc_status": "0",
			"allow_edit": "HR Manager",
			"update_field": "status",
			"update_value": "Open & Approved",
		},
		{
			"state": "Rejected",
			"doc_status": "0",
			"allow_edit": "HR Manager",
			"update_field": "status",
			"update_value": "Rejected",
		},
	]
	transitions = [
		{
			"state": "Pending",
			"action": "Send for Review",
			"next_state": "Manager Review",
			"allowed": "HR User",
			"allow_self_approval": 1,
		},
		{
			"state": "Manager Review",
			"action": "Approve",
			"next_state": "Approved",
			"allowed": "HR Manager",
			"allow_self_approval": 1,
		},
		{
			"state": "Manager Review",
			"action": "Reject",
			"next_state": "Rejected",
			"allowed": "HR Manager",
			"allow_self_approval": 1,
		},
	]
	_create_workflow_if_missing(workflow_name, "Job Requisition", states, transitions)


def ensure_expense_claim_workflow():
	"""Four-level expense claim approval placeholder workflow."""
	workflow_name = "MCX Expense Claim Approval"
	level_states = [
		("Pending L1 Approval", EXPENSE_APPROVAL_ROLES[0]),
		("Pending L2 Approval", EXPENSE_APPROVAL_ROLES[1]),
		("Pending L3 Approval", EXPENSE_APPROVAL_ROLES[2]),
		("Pending L4 Approval", EXPENSE_APPROVAL_ROLES[3]),
	]

	states = [
		{"state": "Draft", "doc_status": "0", "allow_edit": "Employee"},
	]
	transitions = [
		{
			"state": "Draft",
			"action": "Submit for Approval",
			"next_state": "Pending L1 Approval",
			"allowed": "Employee",
			"allow_self_approval": 1,
		},
	]

	for idx, (state_name, role) in enumerate(level_states):
		states.append({"state": state_name, "doc_status": "0", "allow_edit": role})
		next_state = level_states[idx + 1][0] if idx + 1 < len(level_states) else "Approved"
		transitions.append(
			{
				"state": state_name,
				"action": "Approve",
				"next_state": next_state,
				"allowed": role,
				"allow_self_approval": 1,
			}
		)
		transitions.append(
			{
				"state": state_name,
				"action": "Reject",
				"next_state": "Rejected",
				"allowed": role,
				"allow_self_approval": 1,
			}
		)

	states.extend(
		[
			{
				"state": "Approved",
				"doc_status": "1",
				"allow_edit": "HR Manager",
				# Native ExpenseClaim.on_submit requires approval_status, not status
				"update_field": "approval_status",
				"update_value": "Approved",
			},
			{
				"state": "Rejected",
				"doc_status": "0",
				"allow_edit": "HR Manager",
				"update_field": "approval_status",
				"update_value": "Rejected",
			},
		]
	)

	_create_or_sync_workflow(workflow_name, "Expense Claim", states, transitions)


def ensure_leave_application_workflow():
	workflow_name = "MCX Leave Application Approval"
	states = [
		{"state": "Open", "doc_status": "0", "allow_edit": "Employee"},
		{"state": "Pending Approval", "doc_status": "0", "allow_edit": "Leave Approver"},
		{
			"state": "Approved",
			"doc_status": "1",
			"allow_edit": "Leave Approver",
			"update_field": "status",
			"update_value": "Approved",
		},
		{
			"state": "Rejected",
			"doc_status": "0",
			"allow_edit": "Leave Approver",
			"update_field": "status",
			"update_value": "Rejected",
		},
	]
	transitions = [
		{
			"state": "Open",
			"action": "Submit for Approval",
			"next_state": "Pending Approval",
			"allowed": "Employee",
			"allow_self_approval": 1,
		},
		{
			"state": "Pending Approval",
			"action": "Approve",
			"next_state": "Approved",
			"allowed": "Leave Approver",
			"allow_self_approval": 0,
		},
		{
			"state": "Pending Approval",
			"action": "Reject",
			"next_state": "Rejected",
			"allowed": "Leave Approver",
			"allow_self_approval": 0,
		},
	]
	_create_workflow_if_missing(workflow_name, "Leave Application", states, transitions)
