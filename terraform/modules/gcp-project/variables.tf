variable "project_id" {
  description = "Globally unique project ID, e.g. syy-rme-orders-nonprod. Can't be changed later."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{4,28}[a-z0-9]$", var.project_id))
    error_message = "project_id: 6-30 chars, lowercase letters, numbers and hyphens, starting with a letter, not ending with a hyphen."
  }
}

variable "name" {
  description = "Display name of the project (4-30 characters)."
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9' !-]{4,30}$", var.name))
    error_message = "name: 4-30 chars: letters, numbers, spaces, hyphens, single quotes or exclamation marks."
  }
}

variable "folder_id" {
  description = "Numeric ID of the folder the project is created in."
  type        = string
}

variable "billing_account" {
  description = "Billing account ID (XXXXXX-XXXXXX-XXXXXX) the project is linked to."
  type        = string
}

variable "labels" {
  description = "Labels for the project (lowercase keys and values, max 63 characters each)."
  type        = map(string)
  default     = {}
}

variable "activate_apis" {
  description = "APIs to enable on the new project."
  type        = list(string)
  default     = []
}
