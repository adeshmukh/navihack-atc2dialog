output "bucket_name" {
  description = "Name of the provisioned GCS bucket."
  value       = module.gcs_bucket.name
}

output "bucket_url" {
  description = "Console URL for the bucket."
  value       = module.gcs_bucket.url
}
