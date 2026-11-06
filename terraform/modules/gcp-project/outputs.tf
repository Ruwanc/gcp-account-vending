output "project_id" {
  description = "The new project ID."
  value       = google_project.this.project_id
}

output "number" {
  description = "The new project number."
  value       = google_project.this.number
}
