output "name" {
  description = "Bucket name."
  value       = google_storage_bucket.this.name
}

output "url" {
  description = "Console URL for the bucket."
  value       = "https://console.cloud.google.com/storage/browser/${google_storage_bucket.this.name}"
}

output "self_link" {
  description = "Self link of the bucket."
  value       = google_storage_bucket.this.self_link
}
