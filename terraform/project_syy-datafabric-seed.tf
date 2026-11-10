# GCP project requested in ServiceNow RITM0010031 / SCTASK0010035
# Requested for: jeff@sysco.com
# Technical owner: tom@sysco.com | Budget approver: ben@sysco.com
# Written by scripts/new_project.py. Change it through a new request, not by hand.
module "project_syy_datafabric_seed" {
  source = "./modules/gcp-project"

  project_id      = "syy-datafabric-seed"
  name            = "datafabric-seed"
  folder_id       = "REPLACE-000000000000"
  billing_account = "REPLACE-000000-000000-000000"
  activate_apis   = ["cloudresourcemanager.googleapis.com", "serviceusage.googleapis.com"]

  labels = {
    "technical_applicationname" = "data_team"
    "technical_platformowner"   = "tom_sysco_com"
    "business_budgetapprover"   = "ben_sysco_com"
    "business_supportgroup"     = "data_team"
    "servicenow_ritm"           = "ritm0010031"
  }
}

output "project_syy_datafabric_seed_number" {
  description = "Project number of syy-datafabric-seed"
  value       = module.project_syy_datafabric_seed.number
}
