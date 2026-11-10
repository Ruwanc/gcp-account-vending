# GCP project requested in ServiceNow RITM0010032 / SCTASK0010036
# Requested for: jeff@sysco.com
# Technical owner: jack.miller@sysco.com | Budget approver: oliver.smith@sysco.com
# Written by scripts/new_project.py. Change it through a new request, not by hand.
module "project_syy_datafbaric_npx" {
  source = "./modules/gcp-project"

  project_id      = "syy-datafbaric-npx"
  name            = "datafbaric-npx"
  folder_id       = "REPLACE-000000000000"
  billing_account = "REPLACE-000000-000000-000000"
  activate_apis   = ["cloudresourcemanager.googleapis.com", "serviceusage.googleapis.com"]

  labels = {
    "technical_applicationname" = "data_team"
    "technical_platformowner"   = "jack_miller_sysco_com"
    "business_budgetapprover"   = "oliver_smith_sysco_com"
    "business_supportgroup"     = "datateam_support"
    "servicenow_ritm"           = "ritm0010032"
  }
}

output "project_syy_datafbaric_npx_number" {
  description = "Project number of syy-datafbaric-npx"
  value       = module.project_syy_datafbaric_npx.number
}
