# Copyright (c) 2026, Ascra Technologies LLP and contributors
# For license information, please see license.txt

"""Production cutover gates and security validation for MCX HRMS."""

from __future__ import annotations

import frappe

from mcx_hrms.constants import COMPANY_NAME, DEMO_SITE


def run_production_gates(company: str | None = None) -> dict:
	"""Validate demo readiness and document production blockers."""
	company = company or COMPANY_NAME
	checks: list[dict] = []

	checks.append(_gate("Site is demo site", frappe.local.site == DEMO_SITE))
	checks.append(_gate("HRMS installed", "hrms" in frappe.get_installed_apps()))
	checks.append(_gate("India Payroll installed", "india_payroll" in frappe.get_installed_apps()))
	checks.append(_gate("LMS installed", "lms" in frappe.get_installed_apps()))
	checks.append(_gate("MCX HRMS app installed", "mcx_hrms" in frappe.get_installed_apps()))
	checks.append(_gate("MCX Learning AI installed", "mcx_learning_ai" in frappe.get_installed_apps()))

	checks.append(_gate("Company configured", frappe.db.exists("Company", company)))
	checks.append(
		_gate(
			"HR Settings — self-approval prevented",
			bool(frappe.db.get_single_value("HR Settings", "prevent_self_leave_approval")),
		)
	)
	if frappe.db.exists("DocType", "Payroll Settings"):
		ps = frappe.get_single("Payroll Settings")
		statutory_fields = ("enable_epf", "enable_esic", "enable_professional_tax", "enable_lwf")
		checks.append(
			_gate(
				"Payroll Settings — India statutory toggles",
				all(getattr(ps, field, 0) for field in statutory_fields if hasattr(ps, field)),
			)
		)

	checks.append(
		_gate(
			"FY 2026-27 tax slab present (validate before production)",
			frappe.db.exists("Income Tax Slab", "New Tax Regime: 2026-2027"),
			blocker="Confirm notified FY 2026-27 slabs with Finance before live payroll.",
		)
	)
	checks.append(
		_gate(
			"Adrenaline migration extracts received",
			False,
			blocker="Production migration blocked until Adrenaline sample files are provided.",
		)
	)
	checks.append(
		_gate(
			"SSO / SAML configured",
			_has_identity_provider(),
			blocker="Configure identity provider before production cutover.",
		)
	)
	checks.append(
		_gate(
			"Email outbound configured",
			bool(frappe.get_all("Email Account", filters={"enable_outgoing": 1}, limit=1)),
			blocker="Configure SMTP before production notifications.",
		)
	)

	if "mcx_learning_ai" in frappe.get_installed_apps():
		settings = frappe.get_single("MCX Learning AI Settings")
		checks.append(_gate("AI learning features enabled", bool(settings.enabled)))
		if frappe.db.exists("DocType", "MCX AI Settings"):
			checks.append(
				_gate(
					"AI provider key configured (optional for demo)",
					bool(frappe.db.get_single_value("MCX AI Settings", "api_key")),
					blocker="Live AI rerank/chat requires MCX AI Settings API key.",
				)
			)

	checks.append(
		_gate(
			"Training Event LMS bridge fields",
			frappe.db.exists("Custom Field", "Training Event-lms_course")
			and frappe.db.exists("Custom Field", "Training Event-lms_batch"),
		)
	)

	passed = sum(1 for c in checks if c["passed"])
	required_blockers = [c["blocker"] for c in checks if c.get("blocker") and not c["passed"]]

	return {
		"company": company,
		"passed": passed,
		"total": len(checks),
		"demo_ready": passed >= len(checks) - 4,
		"production_ready": passed == len(checks),
		"blockers": required_blockers,
		"checks": checks,
	}


def _has_identity_provider() -> bool:
	for doctype in ("Social Login Key", "SAML Settings", "LDAP Settings"):
		if not frappe.db.exists("DocType", doctype):
			continue
		try:
			if frappe.get_all(doctype, limit=1):
				return True
		except Exception:
			continue
	return False


def _gate(label: str, passed: bool, blocker: str = "") -> dict:
	return {"check": label, "passed": bool(passed), "blocker": blocker}


def print_production_gates_report(company: str | None = None):
	report = run_production_gates(company)
	print(f"\nMCX HRMS Production Gates — {report['passed']}/{report['total']} passed")
	print(f"Demo ready: {report['demo_ready']} | Production ready: {report['production_ready']}\n")
	for row in report["checks"]:
		status = "PASS" if row["passed"] else "FAIL"
		print(f"  [{status}] {row['check']}")
		if row.get("blocker") and not row["passed"]:
			print(f"         Blocker: {row['blocker']}")
	if report["blockers"]:
		print("\nProduction blockers:")
		for blocker in report["blockers"]:
			print(f"  - {blocker}")
	print()
	return report
