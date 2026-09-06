terraform {
  required_version = ">= 1.9.0"

  required_providers {
    kind = {
      source  = "tehcyx/kind"
      version = "0.11.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "3.3.0"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

provider "kind" {}

provider "helm" {
  kubernetes = {
    config_path = module.cluster.kubeconfig_path
  }
}
