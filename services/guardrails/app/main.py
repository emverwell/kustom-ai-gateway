"""Guardrails service: classifies a prompt for injection, then checks PII,
returning a single block/allow decision (with redaction where applicable).

Two HTTP surfaces:
- POST /evaluate — our own convenience shape, {"text": ...} in.
- POST /request  — agentgateway's Webhook prompt-guard contract, verified
  against crates/agentgateway/src/llm/policy/webhook.rs in the agentgateway
  source (not guessed from docs): {"body": {"messages": [...]}} in, an
  untagged Pass/Mask/Reject "action" out.
"""

from __future__ import annotations

from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from pydantic import BaseModel

from .classifier import get_classifier
from .pii import PiiEngine
from .policy import load_policy

app = FastAPI(title="guardrails")

_policy = load_policy()
_pii_engine = PiiEngine(_policy)
_classifier = get_classifier("onnx")

GUARDRAIL_VERDICTS = Counter(
    "guardrail_verdicts_total",
    "Guardrail verdicts by decision and reason",
    ["decision", "reason"],
)


class EvaluateRequest(BaseModel):
    text: str


class EvaluateResponse(BaseModel):
    decision: str  # "block" or "allow"
    text: str
    reasons: list[str]


def _record_verdict(decision: str, reasons: list[str]) -> None:
    for reason in reasons or ["clean"]:
        GUARDRAIL_VERDICTS.labels(decision=decision, reason=reason).inc()


def _classify_and_check(text: str) -> tuple[str, str, list[str]]:
    """Runs the injection classifier, then (if not blocked) the PII engine.
    Returns (decision, resulting_text, reasons)."""
    classifier_verdict = _classifier.classify(text)
    if classifier_verdict.label == "INJECTION":
        return "block", text, ["prompt_injection"]

    pii_verdict = _pii_engine.evaluate(text)
    return pii_verdict.decision, pii_verdict.text, pii_verdict.entities_found


@app.post("/evaluate", response_model=EvaluateResponse)
def evaluate(request: EvaluateRequest) -> EvaluateResponse:
    decision, text, reasons = _classify_and_check(request.text)
    _record_verdict(decision, reasons)
    return EvaluateResponse(decision=decision, text=text, reasons=reasons)


class ChatMessage(BaseModel):
    role: str
    content: str


class PromptMessages(BaseModel):
    messages: list[ChatMessage]


class GuardrailsPromptRequest(BaseModel):
    body: PromptMessages


@app.post("/request")
def guardrail_request(request: GuardrailsPromptRequest) -> dict:
    redacted_messages: list[ChatMessage] = []
    block_reasons: list[str] = []
    any_redacted = False

    for message in request.body.messages:
        decision, text, reasons = _classify_and_check(message.content)
        if decision == "block":
            block_reasons.extend(reasons)
            continue
        if text != message.content:
            any_redacted = True
        redacted_messages.append(ChatMessage(role=message.role, content=text))

    if block_reasons:
        reasons = sorted(set(block_reasons))
        _record_verdict("block", reasons)
        return {"action": {"body": f"blocked: {', '.join(reasons)}", "status_code": 403}}

    if any_redacted:
        _record_verdict("allow", ["redacted"])
        return {"action": {"body": {"messages": [m.model_dump() for m in redacted_messages]}}}

    _record_verdict("allow", [])
    return {"action": {}}


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
