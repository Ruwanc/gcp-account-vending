# GCP project requested in ServiceNow RITM0010022 / SCTASK0010026
# Requested for: t@t.com
# Technical owner: ab@t.com | Budget approver: b@t.com
# Written by scripts/new_project.py. Change it through a new request, not by hand.
module "project_syy_dremx" {
  source = "./modules/gcp-project"

  project_id      = "syy-dremx"
  name            = "dremx"
  folder_id       = "REPLACE-000000000000"
  billing_account = "REPLACE-000000-000000-000000"
  activate_apis   = ["cloudresourcemanager.googleapis.com", "serviceusage.googleapis.com"]

  labels = {
    "technical_applicationname" = "dream"
    "technical_platformowner"   = "ab_t_com"
    "business_budgetapprover"   = "b_t_com"
    "business_supportgroup"     = "abc"
    "servicenow_ritm"           = "ritm0010022"
  }
}

output "project_syy_dremx_number" {
  description = "Project number of syy-dremx"
  value       = module.project_syy_dremx.number
}
