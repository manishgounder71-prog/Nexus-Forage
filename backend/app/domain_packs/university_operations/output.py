from typing import List, Dict, Any, Optional
from app.domain_packs.report_factory import assemble_executive_report

_PROFILE = {
    "title": "UNIVERSITY ACADEMIC OPERATIONS CRISIS REPORT",
    "domain": "UNIVERSITY_OPERATIONS",
    "severity": "CRITICAL ACADEMIC DISRUPTION (per domain pack)",
}

def build_university_operations_executive_report(
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