# Runs as a service account with Project Creator on the target folder and Billing Account User
# on the billing account. Credentials come from GitHub Actions Workload Identity Federation
# (see docs/gcp-setup.md), never from stored keys.
provider "google" {
  default_labels = {
    "managed_by" = "terraform-gcp-account-vending"
  }
}
