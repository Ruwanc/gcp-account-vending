# GCP project requested in ServiceNow RITM0010029 / SCTASK0010033
# Requested for: ruwan@sysco.com
# Technical owner: john@sysco.com | Budget approver: maria@sysco.com
# Written by scripts/new_project.py. Change it through a new request, not by hand.
module "project_syy_dataplatform_seek" {
  source = "./modules/gcp-project"

  project_id      = "syy-dataplatform-seek"
  name            = "dataplatform-seek"
  folder_id       = "REPLACE-000000000000"
  billing_account = "REPLACE-000000-000000-000000"
  activate_apis   = ["cloudresourcemanager.googleapis.com", "serviceusage.googleapis.com"]

  labels = {
    "technical_applicationname" = "seek"
    "technical_platformowner"   = "john_sysco_com"
    "business_budgetapprover"   = "maria_sysco_com"
    "business_supportgroup"     = "seek_support"
    "servicenow_ritm"           = "ritm0010029"
  }
}

output "project_syy_dataplatform_seek_number" {
  description = "Project number of syy-dataplatform-seek"
  value       = module.project_syy_dataplatform_seek.number
}
