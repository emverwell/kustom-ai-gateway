variable "cluster_name" {
  description = "Name of the kind cluster."
  type        = string
}

variable "node_image" {
  description = "Pinned kindest/node image (must include the @sha256 digest for reproducibility)."
  type        = string
}

variable "kubeconfig_path" {
  description = "File path where the generated kubeconfig is written."
  type        = string
}
