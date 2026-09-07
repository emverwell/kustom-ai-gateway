"""Guardrails service: classifies a prompt for injection, then checks PII,
returning a single block/allow decision (with redaction where applicable).

Standalone HTTP API for now — the exact contract agentgateway expects via
AgentgatewayPolicy is a step-6 concern, verified against the live CRD then.
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


@app.post("/evaluate", response_model=EvaluateResponse)
def evaluate(request: EvaluateRequest) -> EvaluateResponse:
    classifier_verdict = _classifier.classify(request.text)
    if classifier_verdict.label == "INJECTION":
        _record_verdict("block", ["prompt_injection"])
        return EvaluateResponse(decision="block", text=request.text, reasons=["prompt_injection"])

    pii_verdict = _pii_engine.evaluate(request.text)
    _record_verdict(pii_verdict.decision, pii_verdict.entities_found)
    return EvaluateResponse(
        decision=pii_verdict.decision,
        text=pii_verdict.text,
        reasons=pii_verdict.entities_found,
    )


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
