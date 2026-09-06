# Architecture decisions

Short rationale for the non-obvious choices in this repo — what was considered
and rejected, and why. These are locked decisions, not open questions; see the
README for the resulting architecture.

## ADR-001: kind, not minikube / k3d / Docker Desktop Kubernetes

**Decision:** Run the whole stack on `kind` (Kubernetes-in-Docker), one
control-plane node + one worker.

**Alternatives considered:** minikube (heavier, VM-backed on some drivers),
k3d (great, but based on k3s, which strips APIs — a lower-fidelity match to
the Gateway API and CRD behavior this project depends on), Docker Desktop's
built-in Kubernetes (single-node only, no multi-node story, not
reproducible outside Docker Desktop).

**Why:** `kind` runs upstream Kubernetes, supports multi-node clusters in
containers, is what `helm/kind-action` uses in GitHub Actions CI, and needs
nothing beyond Docker — so "works on my laptop" and "works in CI" are the
same cluster shape.

## ADR-002: Terraform for infrastructure and third-party Helm; Kustomize for first-party manifests — never mixed

**Decision:** Terraform provisions the cluster and installs third-party Helm
charts (agentgateway, OTel Collector, kube-prometheus-stack). Kustomize owns
every manifest this repo authors (`Gateway`, `HTTPRoute`, guardrails
Deployment, policies). Terraform is never used to template application YAML.

**Alternatives considered:** Terraform's `kubernetes_manifest` /
`helm_release` with inline `values` for everything, including first-party
resources; or a single Helm umbrella chart for the whole app.

**Why:** Terraform is good at lifecycle management of infrastructure (does
this exist, does it need to change, tear it down cleanly) but is a poor
templating language for application manifests — HCL-embedded YAML strings
lose editor tooling, diffing, and `kubectl diff`/`kustomize build` dry-run
ergonomics. Splitting the boundary at "infrastructure vs. manifests we
author" keeps each tool doing what it's good at, and is a distinction a
platform engineering reviewer will recognize immediately.

## ADR-003: Kubernetes Gateway API + agentgateway, not NGINX Ingress or a generic Envoy Gateway

**Decision:** Use the Gateway API (experimental channel, v1.6.x) with the
agentgateway OSS control plane as the `GatewayClass` implementation.

**Alternatives considered:** NGINX Ingress Controller (simplest, most
familiar, but the `Ingress` API has no first-class extension point for
attaching an AI-specific policy like a guardrails webhook); Envoy Gateway or
Istio Gateway (both solid generic Gateway API implementations, but generic —
neither is purpose-built for LLM/agent traffic).

**Why:** The project's subject is an *AI* gateway, not a generic reverse
proxy. agentgateway's `AgentgatewayBackend` / `AgentgatewayPolicy` CRDs are
built around LLM backends and guardrail attachment points, so the resources
this repo authors demonstrate the specific domain (AI gateway policy
enforcement) rather than generic ingress routing that any project would
have.

## ADR-004: onnxruntime with a model baked into the image, not a hosted moderation API

**Decision:** Run ProtectAI's `deberta-v3-base-prompt-injection-v2`, ONNX-exported,
baked into the guardrails image at build time.

**Alternatives considered:** Calling a hosted content-moderation/prompt-injection
API (e.g., a cloud provider's safety endpoint); downloading the model at
container startup.

**Why:** Zero recurring cost and no paid API key is a hard constraint for
this repo. A hosted API also means guardrail behavior depends on an
external service being reachable — bad for a demo meant to run offline and
deterministically. Baking the model in at build time keeps builds hermetic
and CI able to run fully offline, at the cost of a larger image, which is an
acceptable trade for a project that isn't optimizing for image size.

## ADR-005: Presidio + spaCy `en_core_web_sm`, not `en_core_web_lg`

**Decision:** Use the small spaCy English model for Presidio's NLP-based PII
recognizers.

**Alternatives considered:** `en_core_web_lg` (meaningfully better named-entity
recognition, e.g. for `PERSON`).

**Why:** `_lg` pushes the final image well past the ~800MB budget for a
"clones and builds fast on a laptop" demo. The policy config layer (YAML
entity list with per-entity `block | redact | allow`) is the part meant to
demonstrate judgement here, not NER accuracy — `_sm` is enough to prove the
pipeline works end-to-end against the red-team corpus.

## ADR-006: A mock OpenAI-compatible LLM backend as the default, not a real provider

**Decision:** `services/mock-llm/` is a ~80-line deterministic server that
mimics the OpenAI chat-completions API shape. It's the only backend enabled
by default.

**Alternatives considered:** Wiring the gateway to a real provider (OpenAI,
Anthropic, etc.) with a free-tier key.

**Why:** No paid API key, ever, in tests or CI — a free-tier key is still a
credential to manage and a rate limit to hit, and it makes CI non-deterministic
and dependent on an external service being up. A second `AgentgatewayBackend`
pointing at a real provider may exist in the repo for demonstration, but must
be disabled by default via overlay — the golden path never leaves the laptop.

## ADR-007: Chainsaw for Kubernetes e2e, pytest for the guardrails service — not one test framework for both

**Decision:** Chainsaw asserts end-to-end behavior through the live cluster
(a prompt hits the proxy, the right verdict comes back). pytest covers the
guardrails FastAPI app in isolation, against the fixture corpus, without a
cluster.

**Alternatives considered:** Testing everything through Chainsaw/e2e only, or
standing up a full cluster for every guardrails unit test.

**Why:** Unit-level guardrail logic (does this regex + entity list produce
the right action) doesn't need a Kubernetes cluster to verify, and paying
that cost on every test run would make the inner dev loop slow. Matching the
test tool to the layer it's testing — service logic vs. wiring — is why step
5 (guardrails standalone, `pytest` green) is deliberately ordered before
step 6 (guardrails in-cluster, Chainsaw e2e).

## ADR-008: Kyverno + Conftest + Trivy + syft + cosign, even for a demo that never leaves a laptop

**Decision:** In-cluster Kyverno policies (no `:latest`, non-root, resource
limits required) plus Conftest against rendered manifests in CI, a Trivy
image scan, an SBOM via syft, and keyless cosign signing via OIDC.

**Alternatives considered:** Skipping supply-chain tooling entirely, since
uptime/scale/production-hardening are explicitly non-goals for this repo.

**Why:** These aren't about hardening this specific demo for production —
they're evidence that policy-as-code and supply-chain practices are second
nature, which is exactly the "evidence of judgement" signal the repo is
optimizing for. The cost is low (all open-source, all run in free GitHub
Actions minutes) and the signal is high.

## ADR-009: Helm installs stay in Terraform — no ArgoCD / GitOps

**Decision:** The Gateway API CRDs and the agentgateway Helm charts are
installed by Terraform (`terraform/modules/gateway`), applied synchronously
as part of `terraform apply`.

**Alternatives considered:** Installing them via ArgoCD instead, with
Terraform (or a bootstrap script) only standing up ArgoCD itself, and the
rest of the stack defined as ArgoCD `Application` resources synced from this
repo.

**Why:** GitOps earns its cost when there's drift to reconcile across
multiple environments or operators over time — this repo has exactly one
environment, one operator, and a cluster that's destroyed and rebuilt each
session, so there's nothing to drift. Adding ArgoCD would also introduce a
bootstrap chicken-and-egg (something still has to install ArgoCD before it
can take over), turn `task up`'s single synchronous `terraform apply` into a
race against an async reconciliation loop a 5-minute reviewer could catch
mid-sync, split teardown ownership between Terraform and ArgoCD (complicating
the clean `terraform destroy` `task down` relies on), and add a nontrivial
RAM cost on top of an already-tight 8GB budget shared with guardrails, OTel,
Prometheus, and Grafana. Recognizing that a popular pattern doesn't fit a
single-environment ephemeral demo is itself the judgement signal this ADR is
recording.
