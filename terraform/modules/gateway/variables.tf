variable "kubeconfig_path" {
  description = "Path to the kubeconfig for the target cluster (used by the local kubectl invocation that installs the Gateway API CRDs)."
  type        = string
}

variable "gateway_api_version" {
  description = "Pinned Gateway API release tag (experimental channel)."
  type        = string
  default     = "v1.6.1"
}

variable "chart_version" {
  description = "Pinned version shared by the agentgateway-crds and agentgateway Helm charts."
  type        = string
  default     = "1.5.0"
}

variable "namespace" {
  description = "Namespace the agentgateway control plane is installed into."
  type        = string
  default     = "agentgateway-system"
}
