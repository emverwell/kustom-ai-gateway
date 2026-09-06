# kustom-ai-gateway

A local, zero-cost demonstration of Kubernetes platform engineering and AI
gateway implementation: an [agentgateway](https://agentgateway.dev) proxy in
front of an LLM backend, with a guardrails service enforcing prompt-injection
and PII policy, all running on a single-machine [kind](https://kind.sigs.k8s.io/)
cluster and provisioned end-to-end with Terraform.

This is a portfolio project, not a product — see [`CLAUDE.md`](./CLAUDE.md) for
the full design brief, locked stack, and step-by-step build plan.

## Request path

```
client → agentgateway proxy ──→ guardrails webhook (Presidio + ONNX)
                            ←── verdict
                            ──→ mock LLM backend
         proxy + webhook ───→ OTel collector → Prometheus / Grafana
```

## Status

Work in progress, built one step at a time. See the step plan in `CLAUDE.md`
for what's done and what's next.

## Requirements

- Docker
- `kind`
- Terraform
- [Task](https://taskfile.dev/)

## Quickstart

```
task up
```

(Not yet implemented — cluster provisioning lands in a later step.)
