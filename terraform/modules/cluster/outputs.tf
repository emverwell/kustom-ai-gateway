output "cluster_name" {
  description = "Name of the kind cluster."
  value       = kind_cluster.this.name
}

output "kubeconfig_path" {
  description = "File path of the generated kubeconfig."
  value       = kind_cluster.this.kubeconfig_path
}

output "kubeconfig" {
  description = "Generated kubeconfig content."
  value       = kind_cluster.this.kubeconfig
  sensitive   = true
}

output "endpoint" {
  description = "Kubernetes API server URL."
  value       = kind_cluster.this.endpoint
}

output "client_certificate" {
  value     = kind_cluster.this.client_certificate
  sensitive = true
}

output "client_key" {
  value     = kind_cluster.this.client_key
  sensitive = true
}

output "cluster_ca_certificate" {
  value     = kind_cluster.this.cluster_ca_certificate
  sensitive = true
}
