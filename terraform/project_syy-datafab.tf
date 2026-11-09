# GCP project requested in ServiceNow RITM0010023 / SCTASK0010027
# Requested for: ruwan@sysco.com
# Technical owner: nimantha@sysco.com | Budget approver: dale@sysco.com
# Written by scripts/new_project.py. Change it through a new request, not by hand.
module "project_syy_datafab" {
  source = "./modules/gcp-project"

  project_id      = "syy-datafab"
  name            = "datafab"
  folder_id       = "REPLACE-000000000000"
  billing_account = "REPLACE-000000-000000-000000"
  activate_apis   = ["cloudresourcemanager.googleapis.com", "serviceusage.googleapis.com"]

  labels = {
    "technical_applicationname" = "data_engineers"
    "technical_platformowner"   = "nimantha_sysco_com"
    "business_budgetapprover"   = "dale_sysco_com"
    "business_supportgroup"     = "data_support"
    "servicenow_ritm"           = "ritm0010023"
  }
}

output "project_syy_datafab_number" {
  description = "Project number of syy-datafab"
  value       = module.project_syy_datafab.number
}
