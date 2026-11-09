# GCP project requested in ServiceNow RITM0010026 / SCTASK0010030
# Requested for: ruwan@sysco.com
# Technical owner: dan@sysco.com | Budget approver: ben@sysco.com
# Written by scripts/new_project.py. Change it through a new request, not by hand.
module "project_syy_dataproject" {
  source = "./modules/gcp-project"

  project_id      = "syy-dataproject"
  name            = "dataproject"
  folder_id       = "REPLACE-000000000000"
  billing_account = "REPLACE-000000-000000-000000"
  activate_apis   = ["cloudresourcemanager.googleapis.com", "serviceusage.googleapis.com"]

  labels = {
    "technical_applicationname" = "data-team"
    "technical_platformowner"   = "dan_sysco_com"
    "business_budgetapprover"   = "ben_sysco_com"
    "business_supportgroup"     = "data-snow-support"
    "servicenow_ritm"           = "ritm0010026"
  }
}

output "project_syy_dataproject_number" {
  description = "Project number of syy-dataproject"
  value       = module.project_syy_dataproject.number
}
