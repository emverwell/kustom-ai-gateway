# Pinned per kind v0.30.0 release notes: https://github.com/kubernetes-sigs/kind/releases/tag/v0.30.0
locals {
  node_image = "kindest/node:v1.34.0@sha256:7416a61b42b1662ca6ca89f02028ac133a309a2a30ba309614e8ec94d976dc5a"
}

module "cluster" {
  source = "../../modules/cluster"

  cluster_name    = "kustom-ai-gateway"
  node_image      = local.node_image
  kubeconfig_path = "${path.module}/kubeconfig"
}
