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

Work in progress, built one step at a time. Cluster provisioning (Terraform +
kind) is done; the gateway, guardrails service, and observability stack are
next.

## Requirements

- Docker
- `kind`
- Terraform
- [Task](https://taskfile.dev/)

## Quickstart

```
task up
```

Currently this provisions the two-node (`control-plane` + `worker`) kind
cluster via Terraform. The gateway, guardrails service, and observability
stack land in later steps.

```
task down
```

Tears the cluster down.
