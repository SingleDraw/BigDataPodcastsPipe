# This file defines the variables used in the Terraform configuration for Azure resources.
# To use this file in local development, ensure you have the necessary variables set in your environment or provide them in a `terraform.tfvars` file.
# To use this file in CI/CD, ensure the variables are set as environment variables in github actions workflow as follows:
# env:
#   TF_VAR_resource_group_name: ${{ secrets.TF_VAR_resource_group_name }}
#  TF_VAR_location: ${{ secrets.TF_VAR_location }}
# 
# where all variables defined in this file are prefixed with `TF_VAR_` in the GitHub Actions workflow and the values are stored in GitHub Secrets.
variable "resource_group_name" {}
variable "location" {}
variable "storage_account_name" {}
variable "container_registry_name" {}
# variable "container_app_environment_name" {}
