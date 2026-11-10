# GCP project requested in ServiceNow RITM0010033 / SCTASK0010037
# Requested for: jeff@sysco.com
# Technical owner: jack.miller@sysco.com | Budget approver: bobby@sysco.com
# Written by scripts/new_project.py. Change it through a new request, not by hand.
module "project_syy_datafbaric_np" {
  source = "./modules/gcp-project"

  project_id      = "syy-datafbaric-np"
  name            = "datafbaric-np"
  folder_id       = "REPLACE-000000000000"
  billing_account = "REPLACE-000000-000000-000000"
  activate_apis   = ["cloudresourcemanager.googleapis.com", "serviceusage.googleapis.com"]

  labels = {
    "technical_applicationname" = "data_team"
    "technical_platformowner"   = "jack_miller_sysco_com"
    "business_budgetapprover"   = "bobby_sysco_com"
    "business_supportgroup"     = "data_team_support"
    "servicenow_ritm"           = "ritm0010033"
  }
}

output "project_syy_datafbaric_np_number" {
  description = "Project number of syy-datafbaric-np"
  value       = module.project_syy_datafbaric_np.number
}
