from typing import List, Dict, Any, Optional
from app.domain_packs.report_factory import assemble_executive_report

_PROFILE = {
    "title": "PRODUCTION SOFTWARE INCIDENT RESPONSE REPORT",
    "domain": "SOFTWARE_INCIDENT",
    "severity": "PRIORITY PRODUCTION OUTAGE (per domain pack)",
}

def build_software_incident_executive_report(
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