provider "google" {
  project = var.project_id
}

module "gcs_bucket" {
  source = "./modules/gcs_bucket"

  project_id                  = var.project_id
  bucket_name                 = var.bucket_name
  location                    = var.location
  storage_class               = var.storage_class
  force_destroy               = var.force_destroy
  enable_versioning           = var.enable_versioning
  uniform_bucket_level_access = var.uniform_bucket_level_access
  labels                      = var.labels
  lifecycle_rules             = var.lifecycle_rules
}
