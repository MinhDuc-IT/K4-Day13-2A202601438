from __future__ import annotations

import html
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from fastapi import APIRouter
from fastapi.responses import HTMLResponse


LOG_PATH = Path("data/logs.jsonl")
WINDOW_MINUTES = 60
REFRESH_SECONDS = 30

router = APIRouter()


def _percentile(values: list[float], percentile: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(percentile / 100 * len(ordered)) - 1))
    return ordered[index]


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _recent_records(now: datetime | None = None) -> list[dict[str, Any]]:
    if not LOG_PATH.exists():
        return []
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(minutes=WINDOW_MINUTES)
    records: list[dict[str, Any]] = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        timestamp = _parse_timestamp(record.get("ts"))
        if timestamp is not None and timestamp >= cutoff:
            records.append(record)
    return records


def dashboard_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    responses = [record for record in records if record.get("event") == "response_sent"]
    received = [record for record in records if record.get("event") == "request_received"]
    failures = [record for record in records if record.get("event") == "request_failed"]
    latencies = [float(record["latency_ms"]) for record in responses if isinstance(record.get("latency_ms"), (int, float))]
    costs = [float(record["cost_usd"]) for record in responses if isinstance(record.get("cost_usd"), (int, float))]
    tokens_in = [int(record["tokens_in"]) for record in responses if isinstance(record.get("tokens_in"), int)]
    tokens_out = [int(record["tokens_out"]) for record in responses if isinstance(record.get("tokens_out"), int)]
    quality = [float(record["quality_score"]) for record in responses if isinstance(record.get("quality_score"), (int, float))]
    error_types: dict[str, int] = {}
    for failure in failures:
        error_type = str(failure.get("error_type", "unknown"))
        error_types[error_type] = error_types.get(error_type, 0) + 1

    return {
        "latency": {"p50": _percentile(latencies, 50), "p95": _percentile(latencies, 95), "p99": _percentile(latencies, 99)},
        "traffic": {"count": len(received), "rate": len(received) / WINDOW_MINUTES},
        "errors": {"rate": len(failures) / len(received) * 100 if received else 0.0, "breakdown": error_types},
        "cost": sum(costs),
        "tokens": {"input": sum(tokens_in), "output": sum(tokens_out)},
        "quality": mean(quality) if quality else 0.0,
    }


def _panel(title: str, unit: str, threshold: str, body: str) -> str:
    return f"<section class='panel'><h2>{html.escape(title)}</h2><p class='unit'>{html.escape(unit)} · threshold: {html.escape(threshold)}</p>{body}</section>"


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard() -> HTMLResponse:
    metrics = dashboard_metrics(_recent_records())
    latency = metrics["latency"]
    errors = metrics["errors"]
    error_breakdown = ", ".join(f"{html.escape(name)}: {count}" for name, count in errors["breakdown"].items()) or "No errors"
    panels = "".join(
        [
            _panel("Latency percentiles", "milliseconds", "P95 ≤ 3000 ms", f"<div class='values'><b>P50 {latency['p50']:.0f}</b><b>P95 {latency['p95']:.0f}</b><b>P99 {latency['p99']:.0f}</b></div>"),
            _panel("Request traffic", "requests per minute", "≥ 1 request/min", f"<div class='values'><b>{metrics['traffic']['count']} requests</b><b>{metrics['traffic']['rate']:.2f} req/min</b></div>"),
            _panel("Error rate and breakdown", "percent", "≤ 2%", f"<div class='values'><b>{errors['rate']:.2f}% error rate</b><span>{error_breakdown}</span></div>"),
            _panel("Cost over time", "USD", "total ≤ $2.50", f"<div class='values'><b>${metrics['cost']:.6f}</b><span>total in selected window</span></div>"),
            _panel("Input and output tokens", "tokens", "total ≤ 50,000", f"<div class='values'><b>Input {metrics['tokens']['input']}</b><b>Output {metrics['tokens']['output']}</b></div>"),
            _panel("Quality proxy", "score 0–1", "mean ≥ 0.75", f"<div class='values'><b>{metrics['quality']:.2f}</b><span>mean quality score</span></div>"),
        ]
    )
    return HTMLResponse(
        f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta http-equiv='refresh' content='{REFRESH_SECONDS}'><title>Day 13 AI Observability</title>
        <style>body{{font-family:system-ui,sans-serif;background:#f4f7fb;color:#172033;margin:0;padding:28px}}header{{display:flex;justify-content:space-between;align-items:end;margin-bottom:20px}}h1{{margin:0}}.meta,.unit{{color:#5b677d}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}}.panel{{background:white;border-radius:12px;padding:18px;box-shadow:0 2px 10px #17203318}}h2{{font-size:1.05rem;margin:0 0 6px}}.values{{display:flex;gap:14px;flex-wrap:wrap;font-size:1.25rem;margin-top:22px}}.values span{{font-size:.9rem;align-self:center}}</style></head><body>
        <header><div><h1>Day 13 AI Observability</h1><p class='meta'>Source: data/logs.jsonl · time range: last 60 minutes</p></div><p class='meta'>Auto refresh: 30 seconds</p></header><main class='grid'>{panels}</main></body></html>"""
    )
