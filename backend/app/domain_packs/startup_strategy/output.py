from typing import List, Dict, Any, Optional
from app.domain_packs.report_factory import assemble_executive_report
from app.domain_packs.scenario_analyzer import scenario_analyzer

_PROFILE = {
    "title": "STARTUP STRATEGY & VENTURE EXECUTION REPORT",
    "domain": "STARTUP_STRATEGY",
    "severity": "STRATEGIC VENTURE DECISION (per domain pack)",
}

def build_startup_strategy_executive_report(
    prompt: str,
    consensus: Dict[str, Any],
    selected_strategy: str,
    simulations: List[Dict[str, Any]],
    agent_findings: List[Dict[str, Any]],
    evidence: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    report = assemble_executive_report(
        situation=prompt,
        consensus=consensus,
        selected_strategy=selected_strategy,
        simulations=simulations,
        agent_findings=agent_findings,
        evidence=evidence,
        profile=_PROFILE,
    )

    # Preserve domain-specific strategic reasoning, but ONLY as explicitly labeled
    # heuristic estimates (never as measured facts).
    try:
        analysis = scenario_analyzer.analyze_startup_scenario(prompt)
        report["strategic_analysis"] = {
            "runway_status": analysis.get("runway_status"),
            "burn_reduction_target": analysis.get("burn_reduction_target"),
            "executive_recommendation": analysis.get("executive_recommendation"),
            "why_this_strategy": analysis.get("why_this_strategy"),
            "alternative_strategies": analysis.get("alternative_strategies") or [],
            "assumptions": analysis.get("assumptions") or [],
            "risks": analysis.get("risks") or [],
            "next_30_days_plan": analysis.get("next_30_days_plan") or [],
            "decision_triggers": analysis.get("decision_triggers") or [],
            "is_estimate": True,
            "methodology": "scenario_analyzer prompt-categorization heuristic",
            "warning": (
                "All figures, dollar amounts, percentages, and timelines above are heuristic estimates "
                "generated from prompt categorization. They are NOT measurements or verified facts and "
                "must not be presented as such."
            ),
        }
    except Exception:
        report["strategic_analysis"] = {"is_estimate": True, "methodology": "estimate", "warning": "Analysis unavailable."}

    return report