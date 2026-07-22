# MCX HRMS — Client Demo Guide

Walkthrough script for presenting the MCX HRMS stack on `mcx.site`. Built on **native Frappe HRMS, India Payroll, LMS, and ERPNext** — Ascra apps add MCX config, workflows, and LMS AI demos, not a parallel HR product.

Read once beforehand so the flow feels natural.

---

## What you're showing them

| Theme | Message |
|-------|---------|
| **One ERP** | HR, payroll, learning, and (optionally) helpdesk on the same Frappe stack |
| **ESS / MSS** | Employees apply leave & claims; managers approve in Desk |
| **India payroll** | Structure → Payroll Entry → Salary Slip (India Payroll statutory toggles) |
| **Hire to retire** | Requisition → Applicant → Interview → Offer → Onboarding → Appraisal → Exit |
| **Learning** | Training Event linked to LMS Batch + AI recommend / path / assistant demos |

---

## Before the demo — checklist

### Environment

```bash
cd ~/Desktop/frappe-bench
bench --site mcx.site migrate
bench --site mcx.site execute mcx_hrms.setup.demo.setup_demo_site
bench --site mcx.site execute mcx_hrms.setup.transactions.print_seed_transactions_report
bench --site mcx.site execute mcx_hrms.setup.uat.print_uat_report
```

Site URL: `http://mcx.site:8001` (or your hosts mapping).

### Logins (password for all demo users: `demo@123`)

| Persona | User | Use for |
|---------|------|---------|
| HR / Approver | `priya.sharma@mcx.demo` | MSS approvals, recruitment, payroll, exit |
| Employee | `rahul.mehta@mcx.demo` | ESS leave, expense, payslip, LMS AI |
| LMS learner | same Rahul (or LMS demo users from `mcx_learning_ai`) | `/ai-learning`, courses |

Use **three browser profiles** (or normal + 2× Incognito).

### Confirm sample data exists

You should already have (after transaction seed):

- Org hierarchy (`reports_to` → Priya)
- Pending + approved **Leave Application**
- Pending L1 + approved **Expense Claim**
- Employee **Checkins** + **Attendance**
- Draft **Attendance Request** (WFH)
- Submitted **Salary Slips** (prior month) + draft **Payroll Entry** (current month)
- **Appraisal**, **Interview**, **Job Offer**, draft **Employee Separation**
- Bank accounts on employees + company salary bank
- AI recommendations warmed for Rahul

---

## How to open things

| Area | Path |
|------|------|
| Frappe Desk | `/app` |
| Leave Application | `/app/leave-application` |
| Expense Claim | `/app/expense-claim` |
| Employee Checkin | `/app/employee-checkin` |
| Payroll Entry | `/app/payroll-entry` |
| Salary Slip | `/app/salary-slip` |
| Job Opening / Applicant / Interview / Offer | `/app/job-opening` etc. |
| Appraisal | `/app/appraisal` |
| Employee Separation | `/app/employee-separation` |
| Training Event | `/app/training-event` |
| LMS | `/lms` |
| Learning AI demo | `/ai-learning` |
| Helpdesk (optional) | `/helpdesk/` — see `mcx_helpdesk/CLIENT_DEMO_GUIDE.md` |

---

## The demo — 40–50 minutes

Adjust to the client's priorities. Skip Helpdesk unless they ask.

---

### Part 1 — Org & Employee Information (~5 min)

*Login as Priya.*

1. Open **Employee** list — show Priya, Rahul, Anita, Vikram, Meera (branches / grades / departments).
2. Open Rahul → point out **Reports To = Priya**, Leave Approver, Expense Approver, **Salary Mode = Bank**.
3. Optional: **Organization Chart** / department tree.

**Line:** “This is standard ERPNext Employee master — no parallel HR database.”

---

### Part 2 — Leave ESS → MSS (~7 min)

1. Switch to **Rahul**. Create or open the pending **Casual Leave** (`MCX Demo pending leave`).
2. Show leave balance / allocation.
3. Switch to **Priya**. Open the same Leave Application → workflow **Approve**.
4. Show an already-approved leave (Anita) for history.

**Line:** “Workflow is Frappe Workflow on the native Leave Application DocType — configurable without code.”

---

### Part 3 — Expense & advances (~7 min)

1. As **Priya**, open the **Pending L1** expense (Vikram) — walk Approve through L1→L4 (Priya has all MCX Expense Approver roles for the demo).
2. Open the fully approved claim (Rahul) — show sanctioned amount + payable account.
3. Open draft **Employee Advance** (Vikram imprest) — explain submit + Payment Entry path (native HRMS).

**Line:** “Four-level matrix is a **demo Workflow** on native Expense Claim (`approval_status`) — retarget roles to RM → HoD → F&A for MCX policy; not a certified Annexure matrix out of the box.”

---

### Part 4 — Attendance (~5 min)

1. **Employee Checkin** — First In / Last Out rows for recent days (linked to Attendance).
2. **Attendance** — Present marks created via native `mark_attendance_and_link_log`.
3. Open draft **Attendance Request** (Meera, Work From Home) — submit live to create Attendance.

**Line:** “Biometric devices feed the same Employee Checkin DocType (Frappe biometric sync tool in production).”

---

### Part 5 — Payroll (~8 min)

1. **Salary Structure** `MCX Standard Salary Structure` + assignments.
2. Open a submitted **Salary Slip** (prior month) — earnings / deductions / PDF.
3. Open draft **Payroll Entry** (current month) — employees already filled via `fill_employee_details()`.
4. Optional live: **Create Salary Slips** (don’t submit bank entry unless accounts are ready).
5. Point to **India Payroll** settings (EPF / ESIC / PT toggles) and tax slab FY 2026-27.

**Line:** “Payroll is HRMS + india_payroll — not a custom payroll engine.”

---

### Part 6 — Recruitment (~5 min)

1. **Job Opening** — Trading Executive.
2. **Job Applicant** — Arjun Desai.
3. **Interview** — MCX Technical Round scheduled with Priya.
4. **Job Offer** — awaiting response / submitted.

**Line:** “Full ATS path is standard HRMS Recruitment module.”

---

### Part 7 — PMS & Exit (~5 min)

1. **Appraisal Cycle** + Rahul’s **Appraisal** (template / KRAs).
2. **Employee Separation** (Meera demo checklist) — submit to show Project/Tasks from template activities.

**Line:** “Exit checklist is native Employee Separation — letters via Print Format.”

---

### Part 8 — Learning & AI (~8 min)

1. **Training Event** `MCX Compliance Workshop` — show **LMS Course** / **LMS Batch** links.
2. Optional: call sync APIs or show batch enrollment.
3. As **Rahul**, open `/ai-learning`:
   - Recommendations tab → **Open in LMS** deep-link
   - Path curator (draft a path → Approve creates a **published** LMS Program with membership)
   - Assistant search/chat
4. Open `/lms` course catalogue.

**Line:** “LMS is Frappe LMS; AI layer is a thin **Partial PoC** (Annexure #108/#170–172/#174) — recommendations work without an API key (deterministic scoring). Not full Netflix UX or competency-gap AI.”

---

### Optional — Helpdesk (~10 min)

If the client cares about member support, switch to the Helpdesk guide:

`apps/mcx_helpdesk/CLIENT_DEMO_GUIDE.md`

---

## Talking points for gaps (be honest)

If asked about items not in the demo:

| Topic | Honest answer |
|-------|----------------|
| Adrenaline migration | Demo uses seed data; production needs their extracts |
| SSO | Not configured on demo; Frappe SAML/OAuth supported |
| Biometric live feed | Checkins seeded; production uses sync tool / device API |
| Full competency / 360 | Future phase — Skill Map exists; framework is custom build |
| LinkedIn Learning etc. | Not connected; LMS supports content + APIs |
| Bank H2H | Bank file / payment account shown; host-to-host is integration work |

---

## After the demo — reset / re-seed

```bash
bench --site mcx.site execute mcx_hrms.setup.transactions.print_seed_transactions_report
```

Idempotent: safe to re-run. It skips rows that already exist (matched by demo tags / unique keys).

---

## Do not show as “done” in this demo

- Live Adrenaline cutover
- Production SSO
- Full competency framework / succession
- External LXP connectors
- Netflix-style LXP redesign

Those are roadmap / production items — keep the demo on working native flows.
