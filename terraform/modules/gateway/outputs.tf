output "namespace" {
  description = "Namespace the agentgateway control plane is installed into."
  value       = var.namespace
}

output "gateway_class_name" {
  description = "Name of the GatewayClass the agentgateway controller creates and manages (chart default, not a Terraform-managed resource)."
  value       = "agentgateway"
}
