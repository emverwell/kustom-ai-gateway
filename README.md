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

Work in progress, built one step at a time. Cluster provisioning and the
Gateway API + agentgateway control plane are done; the mock LLM route,
guardrails service, and observability stack are next.

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
cluster, installs the Gateway API CRDs, and installs the agentgateway control
plane via Terraform. The mock LLM route, guardrails service, and observability
stack land in later steps.

```
task down
```

Tears the cluster down.
