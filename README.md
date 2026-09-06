# kustom-ai-gateway

A local, zero-cost demonstration of Kubernetes platform engineering and AI
gateway implementation: an [agentgateway](https://agentgateway.dev) proxy in
front of an LLM backend, with a guardrails service enforcing prompt-injection
and PII policy, all running on a single-machine [kind](https://kind.sigs.k8s.io/)
cluster and provisioned end-to-end with Terraform.

This is a portfolio project, not a product. See
[`docs/decisions.md`](./docs/decisions.md) for the rationale behind the
non-obvious architecture choices.

## Request path

```
client → agentgateway proxy ──→ guardrails webhook (Presidio + ONNX)
                            ←── verdict
                            ──→ mock LLM backend
         proxy + webhook ───→ OTel collector → Prometheus / Grafana
```

## Status

Work in progress, built one step at a time. Cluster provisioning, the
Gateway API + agentgateway control plane, and the mock LLM route are done; the
guardrails service and observability stack are next.

## Requirements

- Docker
- `kind`
- Terraform
- `kubectl`
- [Task](https://taskfile.dev/)

## Pinned versions

| Component | Version |
| --- | --- |
| Kubernetes (`kindest/node`) | v1.34.0 |
| `tehcyx/kind` provider | 0.11.0 |
| `hashicorp/helm` provider | 3.3.0 |
| Gateway API (experimental channel) | v1.6.1 |
| `agentgateway` / `agentgateway-crds` charts | 1.5.0 |

## Quickstart

```
task up
```

Currently this provisions the two-node (`control-plane` + `worker`) kind
cluster, installs the Gateway API CRDs and agentgateway control plane via
Terraform, then loads and deploys the mock LLM and its route via Kustomize.
The guardrails service and observability stack land in later steps.

Point `kubectl` (and any other Kubernetes-aware tool, e.g. `k9s`) at this
cluster for the rest of the session:

```
export KUBECONFIG="$(pwd)/terraform/envs/local/kubeconfig"
```

Send a chat-completions request through the proxy end-to-end:

```
kubectl -n kustom-ai-gateway port-forward svc/kustom-ai-gateway 8080:80 &
curl -s http://localhost:8080/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model": "mock-llm", "messages": [{"role": "user", "content": "hello"}]}'
```

```
task down
```

Tears the cluster down.
