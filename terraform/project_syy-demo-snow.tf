# GCP project requested in ServiceNow RITM0010021 / SCTASK0010025
# Requested for: t@t.com
# Technical owner: jane.doe@corp.com | Budget approver: kurt.brochu@corp.com
# Written by scripts/new_project.py. Change it through a new request, not by hand.
module "project_syy_demo_snow" {
  source = "./modules/gcp-project"

  project_id      = "syy-demo-snow"
  name            = "demo-snow"
  folder_id       = "REPLACE-000000000000"
  billing_account = "REPLACE-000000-000000-000000"
  activate_apis   = ["cloudresourcemanager.googleapis.com", "serviceusage.googleapis.com"]

  labels = {
    "technical_applicationname" = "demo"
    "technical_platformowner"   = "jane_doe_corp_com"
    "business_budgetapprover"   = "kurt_brochu_corp_com"
    "business_supportgroup"     = "demo_support"
    "servicenow_ritm"           = "ritm0010021"
  }
}

output "project_syy_demo_snow_number" {
  description = "Project number of syy-demo-snow"
  value       = module.project_syy_demo_snow.number
}
