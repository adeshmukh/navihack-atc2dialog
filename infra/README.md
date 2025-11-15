# Infrastructure

This folder contains Terraform configuration for provisioning Google Cloud Platform resources that the app depends on. The initial setup provisions a single Google Cloud Storage (GCS) bucket using a reusable module so the pattern can be extended for additional environments and resources.

## Layout

```
infra/
├── backend.tf.example   # Optional remote state backend (copy to backend.tf)
├── main.tf              # Root module wiring and module instantiation
├── outputs.tf           # Root-level outputs
├── variables.tf         # Input variables (used by all environments)
├── versions.tf          # Required Terraform and provider versions
├── terraform.tfvars.example
└── modules/
    └── gcs_bucket/      # Reusable module for creating buckets
```

## Prerequisites

- Terraform >= 1.6 installed locally (see `versions.tf`).
- Access to a GCP project with permissions to create storage buckets.
- Application Default Credentials (ADC) available (for example via `gcloud auth application-default login`).

## Remote State (optional)

If you plan to use a remote backend, copy `backend.tf.example` to `backend.tf` and adjust the bucket, prefix, and project values. Leaving the example file untouched prevents leaking backend credentials and allows local state for quick experiments.

## Usage

1. Duplicate the example tfvars file and populate required values:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```
2. Adjust any variable overrides (bucket name, location, labels, etc.).
3. Initialize and review the execution plan:
   ```bash
   terraform -chdir=infra init
   terraform -chdir=infra plan
   ```
4. Apply when ready:
   ```bash
   terraform -chdir=infra apply
   ```

## Extending

- Add more modules under `infra/modules/` following the same structure.
- Instantiate additional modules (or environments) by referencing them from new root modules or `terragrunt` wrappers.
- Keep shared variables in `variables.tf` and override them via tfvars per environment or workspace.
