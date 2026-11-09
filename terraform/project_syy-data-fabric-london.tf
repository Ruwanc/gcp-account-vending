# GCP project requested in ServiceNow RITM0010027 / SCTASK0010031
# Requested for: ruwan@sysco.com
# Technical owner: john@sysco.com | Budget approver: ben@sysco.com
# Written by scripts/new_project.py. Change it through a new request, not by hand.
module "project_syy_data_fabric_london" {
  source = "./modules/gcp-project"

  project_id      = "syy-data-fabric-london"
  name            = "data-fabric-london"
  folder_id       = "REPLACE-000000000000"
  billing_account = "REPLACE-000000-000000-000000"
  activate_apis   = ["cloudresourcemanager.googleapis.com", "serviceusage.googleapis.com"]

  labels = {
    "technical_applicationname" = "datafabric"
    "technical_platformowner"   = "john_sysco_com"
    "business_budgetapprover"   = "ben_sysco_com"
    "business_supportgroup"     = "datafabric"
    "servicenow_ritm"           = "ritm0010027"
  }
}

output "project_syy_data_fabric_london_number" {
  description = "Project number of syy-data-fabric-london"
  value       = module.project_syy_data_fabric_london.number
}
