variable "project_id" {
  description = "Project ID where the bucket should live."
  type        = string
}

variable "bucket_name" {
  description = "Globally-unique bucket name."
  type        = string
}

variable "location" {
  description = "Bucket location/region."
  type        = string
}

variable "storage_class" {
  description = "Storage class to assign to the bucket."
  type        = string
  default     = "STANDARD"
}

variable "force_destroy" {
  description = "Delete all objects when destroying the bucket."
  type        = bool
  default     = false
}

variable "enable_versioning" {
  description = "Enable object versioning."
  type        = bool
  default     = true
}

variable "uniform_bucket_level_access" {
  description = "Whether uniform bucket-level access is enforced."
  type        = bool
  default     = true
}

variable "labels" {
  description = "Labels applied to the bucket."
  type        = map(string)
  default     = {}
}

variable "lifecycle_rules" {
  description = "Lifecycle rules for object management."
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
