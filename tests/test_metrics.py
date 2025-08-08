import json

from src.metrics import MetricsManager


def test_metrics_record(tmp_path, monkeypatch):
    path = tmp_path / "metrics.json"
    mm = MetricsManager(path=str(path))
    mm.record_request(model="gpt-4", used_fallback=False, success=True, response_time_ms=120, primary_attempt=True)
    mm.record_request(model="gpt-4o-mini", used_fallback=True, success=True, response_time_ms=80, primary_attempt=False)

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["totals"]["requests"] == 2
    assert data["totals"]["success"] == 2
    assert data["llm"]["primary_attempts"] == 1
    assert data["llm"]["fallback_attempts"] == 1
    assert data["timings"]["response_ms_count"] == 2
