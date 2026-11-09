# GCP project requested in ServiceNow RITM0010028 / SCTASK0010032
# Requested for: ruwan@sysco.com
# Technical owner: john@sysco.com | Budget approver: ben@sysco.com
# Written by scripts/new_project.py. Change it through a new request, not by hand.
module "project_syy_data_platform_np_1" {
  source = "./modules/gcp-project"

  project_id      = "syy-data-platform-np-1"
  name            = "data-platform-np-1"
  folder_id       = "REPLACE-000000000000"
  billing_account = "REPLACE-000000-000000-000000"
  activate_apis   = ["cloudresourcemanager.googleapis.com", "serviceusage.googleapis.com"]

  labels = {
    "technical_applicationname" = "data-team"
    "technical_platformowner"   = "john_sysco_com"
    "business_budgetapprover"   = "ben_sysco_com"
    "business_supportgroup"     = "data-snow"
    "servicenow_ritm"           = "ritm0010028"
  }
}

output "project_syy_data_platform_np_1_number" {
  description = "Project number of syy-data-platform-np-1"
  value       = module.project_syy_data_platform_np_1.number
}
