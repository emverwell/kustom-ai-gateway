# The Gateway API experimental-channel CRDs are too large for a client-side
# `kubectl apply` (they exceed the last-applied-configuration annotation size
# limit) and must be applied with --server-side. Terraform's kubernetes
# provider can't install CRDs and consume them in the same plan (the schema
# for a not-yet-installed CRD isn't known at plan time), so we shell out to
# kubectl via the built-in terraform_data resource instead — no extra
# provider required.
resource "terraform_data" "gateway_api_crds" {
  triggers_replace = [var.gateway_api_version, var.kubeconfig_path]

  provisioner "local-exec" {
    command = "kubectl --kubeconfig ${var.kubeconfig_path} apply --server-side -f https://github.com/kubernetes-sigs/gateway-api/releases/download/${var.gateway_api_version}/experimental-install.yaml"
  }
}

resource "helm_release" "agentgateway_crds" {
  name             = "agentgateway-crds"
  namespace        = var.namespace
  create_namespace = true
  chart            = "oci://cr.agentgateway.dev/charts/agentgateway-crds"
  version          = var.chart_version

  depends_on = [terraform_data.gateway_api_crds]
}

# gatewayClassName / controllerName are left at chart defaults ("agentgateway"
# / "agentgateway.dev/agentgateway") — the controller creates and reconciles
# that GatewayClass itself, we don't author it.
resource "helm_release" "agentgateway" {
  name      = "agentgateway"
  namespace = var.namespace
  chart     = "oci://cr.agentgateway.dev/charts/agentgateway"
  version   = var.chart_version

  depends_on = [helm_release.agentgateway_crds]
}
