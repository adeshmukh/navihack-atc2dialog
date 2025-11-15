variable "project_id" {
  description = "The Google Cloud project ID where resources will be created."
  type        = string
}

variable "location" {
  description = "Primary location/region for the bucket (for example, US or us-central1)."
  type        = string
  default     = "US"
}

variable "bucket_name" {
  description = "Globally-unique name for the GCS bucket."
  type        = string
}

variable "storage_class" {
  description = "Storage class to use for the bucket."
  type        = string
  default     = "STANDARD"
}

variable "force_destroy" {
  description = "Whether to delete all contained objects when destroying the bucket."
  type        = bool
  default     = false
}

variable "enable_versioning" {
  description = "Enable object versioning on the bucket."
  type        = bool
  default     = true
}

variable "uniform_bucket_level_access" {
  description = "Enforce uniform bucket-level access instead of fine-grained ACLs."
  type        = bool
  default     = true
}

variable "labels" {
  description = "Key/value labels applied to the bucket."
  type        = map(string)
  default     = {}
}

variable "lifecycle_rules" {
  description = "Lifecycle rules to attach to the bucket (see terraform.tfvars.example)."
  type = list(object({
    action = object({
      type          = string
      storage_class = optional(string)
    })
    condition = object({
      age                   = optional(number)
      created_before        = optional(string)
      with_state            = optional(string)
      matches_storage_class = optional(list(string))
      num_newer_versions    = optional(number)
    })
  }))
  default = []
}
