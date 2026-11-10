# GCP project requested in ServiceNow RITM0010030 / SCTASK0010034
# Requested for: ruwan@sysco.com
# Technical owner: john@sysco.com | Budget approver: ben@sysco.com
# Written by scripts/new_project.py. Change it through a new request, not by hand.
module "project_syy_dataplatform_sbx_np" {
  source = "./modules/gcp-project"

  project_id      = "syy-dataplatform-sbx-np"
  name            = "dataplatform-sbx-np"
  folder_id       = "REPLACE-000000000000"
  billing_account = "REPLACE-000000-000000-000000"
  activate_apis   = ["cloudresourcemanager.googleapis.com", "serviceusage.googleapis.com"]

  labels = {
    "technical_applicationname" = "datateam"
    "technical_platformowner"   = "john_sysco_com"
    "business_budgetapprover"   = "ben_sysco_com"
    "business_supportgroup"     = "datasupport"
    "servicenow_ritm"           = "ritm0010030"
  }
}

output "project_syy_dataplatform_sbx_np_number" {
  description = "Project number of syy-dataplatform-sbx-np"
  value       = module.project_syy_dataplatform_sbx_np.number
}
