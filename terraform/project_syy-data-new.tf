# GCP project requested in ServiceNow RITM0012344 / SCTASK0012344
# Requested for: t@t.com
# Technical owner: ta@t.com | Budget approver: b@t.com
# Written by scripts/new_project.py. Change it through a new request, not by hand.
module "project_syy_data_new" {
  source = "./modules/gcp-project"

  project_id      = "syy-data-new"
  name            = "data-new"
  folder_id       = "REPLACE-000000000000"
  billing_account = "REPLACE-000000-000000-000000"
  activate_apis   = ["cloudresourcemanager.googleapis.com", "serviceusage.googleapis.com"]

  labels = {
    "technical_applicationname" = "dream_team"
    "technical_platformowner"   = "ta_t_com"
    "business_budgetapprover"   = "b_t_com"
    "business_supportgroup"     = "test_snow"
    "servicenow_ritm"           = "ritm0012344"
  }
}

output "project_syy_data_new_number" {
  description = "Project number of syy-data-new"
  value       = module.project_syy_data_new.number
}
