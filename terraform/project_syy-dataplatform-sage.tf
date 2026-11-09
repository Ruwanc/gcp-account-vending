# GCP project requested in ServiceNow RITM0010025 / SCTASK0010029
# Requested for: ruwan@sysco.com
# Technical owner: john@sysco.com | Budget approver: adith@sysco.com
# Written by scripts/new_project.py. Change it through a new request, not by hand.
module "project_syy_dataplatform_sage" {
  source = "./modules/gcp-project"

  project_id      = "syy-dataplatform-sage"
  name            = "dataplatform-sage"
  folder_id       = "REPLACE-000000000000"
  billing_account = "REPLACE-000000-000000-000000"
  activate_apis   = ["cloudresourcemanager.googleapis.com", "serviceusage.googleapis.com"]

  labels = {
    "technical_applicationname" = "sage-platform"
    "technical_platformowner"   = "john_sysco_com"
    "business_budgetapprover"   = "adith_sysco_com"
    "business_supportgroup"     = "sage-platform"
    "servicenow_ritm"           = "ritm0010025"
  }
}

output "project_syy_dataplatform_sage_number" {
  description = "Project number of syy-dataplatform-sage"
  value       = module.project_syy_dataplatform_sage.number
}
