app_name = "mcx_hrms"
app_title = "MCX HRMS"
app_publisher = "Ascra Technologies LLP"
app_description = "MCX HRMS demo setup with workflows and LMS training bridge"
app_email = "sourav@clapgrow.com"
app_license = "mit"

required_apps = ["hrms"]

fixtures = [
	{
		"dt": "Custom Field",
		"filters": [["name", "in", ["Training Event-lms_course", "Training Event-lms_batch"]]],
	},
]

after_install = "mcx_hrms.setup.install.after_install"

doc_events = {
	"Training Event": {
		"on_submit": "mcx_hrms.mcx_hrms.training_bridge.on_training_event_submit",
	},
}
