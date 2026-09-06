# kustom-ai-gateway — working agreement

## What this repo is

A public portfolio project demonstrating Kubernetes platform engineering and AI
gateway implementation. It runs entirely locally on `kind` at zero cost. It is
**not** a product, not a startup MVP, and not something that needs to be
production-hardened. The audience is a hiring manager for an AI Platform /
Platform Engineering / SRE role who will spend five minutes in this repo.

The repo must therefore optimise for, in order:

1. **Reproducibility** — `task up` takes a clean machine to a working demo.
2. **Legibility** — a reviewer understands the architecture from the README.
3. **Evidence of judgement** — pinned versions, tests, policy gates, an
   evaluation corpus for the guardrail.

Uptime, scale, and feature completeness are explicitly *not* goals.

## How I want you to work with me (important)

I am building this to **learn the stack**, not to receive a finished repo.
Please follow this working mode:

- **One step at a time.** Do the current step only. Stop at the end of it and
  wait for me to confirm before starting the next. Do not run ahead.
- **Explain before you act.** Before writing files or running commands, tell me
  in a few sentences what you're about to do and why this approach over the
  obvious alternative. I want the reasoning, not just the artifact.
- **Small commits.** One commit per step, conventional commit messages.
- **Make me run things.** Where a command is instructive (inspecting CRDs,
  reading gateway status, curling the proxy), give me the command to run rather
  than running it yourself, and tell me what a correct result looks like.
- **Push back on me.** If I ask for something that is a bad idea for this
  project's goals, say so directly and explain the tradeoff. Don't just comply.
- **No large scaffolds.** Never generate ten files at once. If a step seems to
  need that, it's really several steps — propose the split.

When a step is finished, end with a short "what you just learned" summary: the
two or three concepts that step actually taught, in plain language.

## Locked stack — do not substitute without asking

**Cluster and IaC**
- `kind`, Kubernetes v1.34, one control-plane + one worker
- Terraform (providers: `tehcyx/kind`, `hashicorp/helm`, `hashicorp/kubernetes`)
- Taskfile for the developer entrypoint
- Kustomize for first-party manifests — **Terraform must not template app YAML**.
  Terraform owns infrastructure and third-party Helm releases; Kustomize owns
  manifests we author.

**Gateway**
- Kubernetes Gateway API v1.6.x CRDs, experimental channel, applied
  `--server-side`
- agentgateway OSS control plane, two Helm charts:
  `oci://cr.agentgateway.dev/charts/agentgateway-crds` and
  `oci://cr.agentgateway.dev/charts/agentgateway`
- **Pin an exact chart version** and record it in the README. The policy CRDs
  have changed shape repeatedly through 2026; an unpinned repo will be broken
  for anyone who clones it in three months.
- Resources we author: `Gateway`, `HTTPRoute`, `AgentgatewayBackend`,
  `AgentgatewayPolicy`

**Guardrails service** (`services/guardrails/`)
- Python 3.12, FastAPI, uvicorn, dependencies managed with `uv`
- `onnxruntime` (CPU) running ProtectAI `deberta-v3-base-prompt-injection-v2`,
  ONNX-exported and **baked into the image at build time** — no runtime model
  downloads, so builds are hermetic and CI works offline
- `presidio-analyzer` + `presidio-anonymizer` for PII, using spaCy
  `en_core_web_sm` (not `_lg` — keeps the image near 800MB)
- Policy is config-driven: a YAML entity list (EMAIL, IBAN, CREDIT_CARD, PERSON,
  plus a custom regex for a fake internal project codename) with a per-entity
  action of `block | redact | allow`
- Two backend implementations behind one interface: `onnx` (default) and
  `ollama` (stub, disabled) — demonstrates the abstraction without the dependency
- Distroless final image, non-root, `/healthz`, `/readyz`, `/metrics`

**Upstream LLM**
- A mock OpenAI-compatible server (`services/mock-llm/`, ~80 lines, deterministic
  responses) is the default backend.
- **Never call a paid LLM provider from tests or CI.** A second
  `AgentgatewayBackend` pointing at a real provider may exist but must be
  disabled by default via overlay.

**Observability**
- OTel Collector (deployment mode) → Prometheus + Grafana, via Helm, with
  resource requests trimmed for kind
- One committed Grafana dashboard JSON: request latency p50/p95, guardrail
  verdicts by category, blocked-vs-passed ratio, token counts

**CI and quality gates**
- GitHub Actions: `helm/kind-action`, full Terraform apply, then e2e
- Chainsaw for Kubernetes e2e assertions; pytest for the guardrails service
- tflint, Checkov, terraform-docs; Kyverno in-cluster (no `:latest`, non-root,
  resource limits required) plus Conftest on rendered manifests in CI
- Trivy image scan, syft SBOM, cosign keyless signing via OIDC
- pre-commit locally

## Repo layout

```
terraform/modules/{cluster,gateway,guardrails,observability}
terraform/envs/local/
k8s/base/  k8s/overlays/{local,ci}/
services/guardrails/{app,tests}/
services/mock-llm/
tests/{chainsaw,corpus}/
docs/                     # MkDocs, published to GitHub Pages
.github/workflows/
Taskfile.yaml
```

## Request path

```
client → agentgateway proxy ──→ guardrails webhook (Presidio + ONNX)
                            ←── verdict
                            ──→ mock LLM backend
         proxy + webhook ───→ OTel collector → Prometheus / Grafana
```

## Step plan

Step 1 is complete before this file is handed over. Work through the rest in
order, stopping after each for my confirmation.

1. **Scaffold** — repo created, directory tree, `.gitignore`, Taskfile stub,
   README stub. *(done)*
2. **Cluster under Terraform** — `terraform/modules/cluster` + `envs/local`,
   wired to `task up` / `task down`. Success: a two-node kind cluster comes up
   and down reproducibly from `terraform apply`.
3. **Gateway API + agentgateway control plane** — CRDs and both Helm charts via
   the Terraform helm provider, pinned. Success: the `agentgateway`
   GatewayClass reports `ACCEPTED: True`.
4. **Mock LLM + first route** — build and load the mock backend image into kind,
   create a `Gateway` and `HTTPRoute`, port-forward and curl it. Success: a
   chat-completions request returns 200 through the proxy.
5. **Guardrails service, standalone** — FastAPI app, Presidio + ONNX classifier,
   YAML policy config, unit tests. Run and test it *outside* Kubernetes first.
   Success: `pytest` green against the fixture corpus.
6. **Guardrails in-cluster and wired up** — containerise, load into kind, deploy
   via Kustomize, attach with `AgentgatewayPolicy`. Success: a prompt containing
   an IBAN is redacted and an injection attempt is blocked, both observed at the
   proxy.
7. **Red-team corpus and e2e** — `tests/corpus/` with ~20 prompts and expected
   verdicts, half adversarial; Chainsaw e2e asserting the whole path.
8. **Observability** — OTel Collector, Prometheus, Grafana, committed dashboard.
9. **CI** — the full apply-and-test loop in GitHub Actions, plus tflint,
   Checkov, Conftest, Trivy, syft, cosign.
10. **Docs and demo** — MkDocs site on GitHub Pages, architecture diagram,
    asciinema recording embedded in the README, a "threat model → policy → test"
    table.

## Standing constraints

- Zero recurring cost. Nothing in this repo may require a paid cloud account,
  a paid API key, or a credit card to run.
- Pin every chart, image, and model version explicitly. No `latest`, no
  floating tags, no unversioned `helm repo add`.
- Everything must run on a laptop with 8GB of free RAM.
- Secrets, even fake ones, never land in git. Use Kustomize secret generators
  with committed `.env.example` files.
- If a manifest, chart value, or CRD field is uncertain against the pinned
  version, check the live CRD with `kubectl explain` rather than guessing from
  memory — the API has moved a lot recently.
