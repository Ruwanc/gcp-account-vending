# Sample module: replace with your organisation's real project module if you have one
# (set module_source in config/project-defaults.json).
resource "google_project" "this" {
  # checkov:skip=CKV2_GCP_5:Audit logging is set once at organisation/folder level, inherited by every project
  name            = var.name
  project_id      = var.project_id
  folder_id       = var.folder_id
  billing_account = var.billing_account
  labels          = var.labels

  # No default network with wide-open firewall rules.
  auto_create_network = false
  # terraform destroy can't delete the project.
  deletion_policy = "PREVENT"

  lifecycle {
    # Removing a project file must never delete a real GCP project by accident.
    prevent_destroy = true
  }
}

resource "google_project_service" "apis" {
  for_each = toset(var.activate_apis)

  project            = google_project.this.project_id
  service            = each.value
  disable_on_destroy = false
}
