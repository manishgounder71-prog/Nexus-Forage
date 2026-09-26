from typing import List, Dict, Any, Optional
from app.domain_packs.report_factory import assemble_executive_report

_PROFILE = {
    "title": "AUTONOMOUS ENTERPRISE CRISIS RESPONSE REPORT",
    "domain": "ENTERPRISE_CRISIS",
    "severity": "CRITICAL ENTERPRISE / INFRASTRUCTURE INCIDENT (severity per domain pack)",
}

def build_enterprise_crisis_executive_report(
    prompt: str,
    consensus: Dict[str, Any],
    selected_strategy: str,
    simulations: List[Dict[str, Any]],
    agent_findings: List[Dict[str, Any]],
    evidence: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return assemble_executive_report(
        situation=prompt,
        consensus=consensus,
        selected_strategy=selected_strategy,
        simulations=simulations,
        agent_findings=agent_findings,
        evidence=evidence,
        profile=_PROFILE,
    )