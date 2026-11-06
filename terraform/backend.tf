# Remote state. Replace the placeholder with your state bucket (versioning on).
terraform {
  backend "gcs" {
    bucket = "REPLACE-terraform-state-bucket"
    prefix = "gcp-account-vending"
  }
}
