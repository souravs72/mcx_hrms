# MCX HRMS

Frappe app for MCX HRMS demo setup: idempotent seed data, approval workflows, sample transactions, and LMS training bridge.

## Features

- **Demo seed** for `mcx.site`: company, org structure, leave/payroll basics, employees, recruitment, training
- **Demo transactions**: leave, expense, checkins/attendance, salary slips, payroll entry, appraisal, interview/offer, separation
- **Workflows**: Job Requisition, 4-level Expense Claim, Leave Application
- **LMS bridge**: sync Training Event attendees to LMS Batch; write back completion to Training Result
- **UAT runner**: validates masters + demo transactions
- **Client demo guide**: [`CLIENT_DEMO_GUIDE.md`](CLIENT_DEMO_GUIDE.md)

## Requirements

- Frappe v16+
- HRMS + ERPNext (`required_apps = ["hrms"]`)
- LMS (optional — training bridge activates when installed)

## Install

```bash
bench get-app /path/to/mcx_hrms
bench --site mcx.site install-app mcx_hrms
bench --site mcx.site migrate
```

### Demo mode

Demo seed runs automatically on `mcx.site` during install. Disable via `site_config.json`:

```json
{ "mcx_hrms_demo_mode": false }
```

Re-run demo seed + transactions:

```bash
bench --site mcx.site execute mcx_hrms.setup.demo.setup_demo_site
bench --site mcx.site execute mcx_hrms.setup.transactions.print_seed_transactions_report
```

### UAT checklist

```bash
bench --site mcx.site execute mcx_hrms.setup.uat.print_uat_report
```

### Training bridge APIs

```python
# Enroll attendees into linked LMS Batch
frappe.call("mcx_hrms.api.training.sync_attendees_to_lms", training_event="...")

# Write LMS progress to Training Result
frappe.call("mcx_hrms.api.training.sync_lms_completion", training_event="...")
```

### Production gates

```bash
bench --site mcx.site execute mcx_hrms.setup.production_gates.print_production_gates_report
```

## License

MIT
