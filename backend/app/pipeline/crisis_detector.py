"""
crisis_detector.py — detects crisis-grade conditions from correlated events.

Combines deterministic rules (single critical alert, deploy + spike combo) with
statistical signals (error-rate and latency deviation from recent baselines).
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional

def _hours_ago(dt: str) -> float:
    try:
        ts = datetime.fromisoformat(dt.replace("Z", "+00:00"))
    except Exception:
        return float("inf")
    now = datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
        now = now.replace(tzinfo=timezone.utc)
    return max((now - ts).total_seconds() / 3600.0, 0.0)


class CrisisEngine:
    def __init__(self):
        self._crisis_handler = None

    def on_crisis(self, handler):
        self._crisis_handler = handler

    def evaluate_incidents(self, incidents: List[Dict]) -> List[Dict]:
        """Runs crisis rules against a batch of incidents; returns crisis-grade ones."""
        crises = []
        for inc in incidents:
            verdict = self.evaluate(inc)
            if verdict["is_crisis"]:
                crises.append(verdict)
        return crises

    def evaluate(self, incident: Dict) -> Dict:
        severity = (incident.get("severity") or "info").lower()
        evidence = incident.get("source_events") or []
        confidence = incident.get("confidence") or 0.0
        meta = incident.get("meta") or {}
        event_types = [str(e.get("event_type", "")).upper() for e in evidence]

        reasons = []
        signals = []
        crisis_points = 0.0

        # 1. Critical severity alert
        if severity == "critical":
            reasons.append("critical-severity-alert")
            signals.append("✓ Critical service failure")
            crisis_points += 0.35
        elif severity == "high":
            crisis_points += 0.20

        # 2. Deployment recency
        deploy_recency = meta.get("deployment_hours_ago")
        if meta.get("deployment_recent") or "DEPLOYMENT" in event_types or (deploy_recency is not None and deploy_recency <= 0.5):
            reasons.append("recent-deployment-coinciding")
            signals.append("✓ Recent deployment detected (<30m)")
            crisis_points += 0.25

        # 3. Database degradation
        if any("DATABASE" in t or "DB" in t for t in event_types):
            reasons.append("database-degradation")
            signals.append("✓ Database degradation detected")
            crisis_points += 0.20

        # 4. Customer impact
        if any("CUSTOMER" in t or "SUPPORT" in t or "COMPLAINT" in t for t in event_types):
            reasons.append("customer-impact")
            signals.append("✓ Customer impact detected")
            crisis_points += 0.20

        # 5. Multi-signal correlation
        if len(evidence) >= 3:
            reasons.append(f"multi-signal({len(evidence)})")
            signals.append(f"✓ Multi-signal correlation ({len(evidence)} independent sources)")
            crisis_points += 0.15

        # 6. Statistical signals (Error rate and Latency)
        error_rates = [
            float(str(e.get("error_rate")).replace("%", ""))
            for e in evidence
            if e.get("error_rate")
        ]
        if error_rates and max(error_rates) >= 30:
            reasons.append(f"error-rate-{int(max(error_rates))}%")
            signals.append(f"✓ Error rate exceeded threshold ({int(max(error_rates))}%)")
            crisis_points += 0.25

        lats = [e.get("avg_latency_ms") for e in evidence if e.get("avg_latency_ms")]
        if lats and max(lats) > 1000:
            reasons.append(f"latency-deviation-{int(max(lats))}ms")
            signals.append(f"✓ Latency deviation exceeded 1000ms ({int(max(lats))}ms)")
            crisis_points += 0.15

        # Final crisis score normalized
        crisis_score = round(min(crisis_points, 1.0), 2)
        is_crisis = bool(reasons) and crisis_score >= 0.35

        priority = "P1" if is_crisis and crisis_score >= 0.60 else ("P2" if is_crisis else "P3")
        final_confidence = round(max(confidence, crisis_score if is_crisis else 0.4), 2)

        return {
            "incident": incident,
            "is_crisis": is_crisis,
            "crisis_score": crisis_score,
            "reasons": reasons,
            "signals": signals,
            "priority": priority,
            "confidence": final_confidence,
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }


crisis_engine = CrisisEngine()