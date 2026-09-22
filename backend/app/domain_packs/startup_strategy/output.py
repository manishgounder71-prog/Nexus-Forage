from typing import List, Dict, Any
from app.domain_packs.scenario_analyzer import scenario_analyzer

def build_startup_strategy_executive_report(
    prompt: str,
    consensus: Dict[str, Any],
    selected_strategy: str,
    simulations: List[Dict[str, Any]],
    agent_findings: List[Dict[str, Any]]
) -> Dict[str, Any]:
    # Dynamically extract and analyze metrics, risks, plans, and options from the user's prompt
    analysis = scenario_analyzer.analyze_startup_scenario(prompt)
    
    # Priority to consensus if returned by parliament
    rec_strategy = consensus.get("selected_strategy") or analysis["recommended_strategy"]
    
    # If selected_strategy from simulations/consensus is provided, format it
    if selected_strategy and "PLAN_" in str(selected_strategy):
        matching_sim = next((s for s in simulations if s.get("id") == selected_strategy), None)
        if matching_sim:
            rec_strategy = f"{matching_sim.get('id')}: {matching_sim.get('title')}"

    return {
        "title": "🚀 STARTUP STRATEGY & VENTURE EXECUTION REPORT",
        "domain": "STARTUP_STRATEGY",
        "situation": analysis["situation"],
        "severity": analysis["severity"],
        "recommended_strategy": rec_strategy,
        "estimated_recovery": "~21-30 Days Execution Window",
        "confidence": f"{int(consensus.get('consensus_score', 0.92) * 100)}%",
        "why_this_strategy": analysis["why_this_strategy"],
        "executive_recommendation": analysis["executive_recommendation"],
        "runway_status": analysis["runway_status"],
        "burn_reduction_target": analysis["burn_reduction_target"],
        "alternative_strategies": analysis["alternative_strategies"],
        "assumptions": analysis["assumptions"],
        "risks": analysis["risks"],
        "next_30_days_plan": analysis["next_30_days_plan"],
        "decision_triggers": analysis["decision_triggers"],
        "dissenting_opinions": consensus.get("dissenting_agents", analysis["dissenting_opinions"]),
        "red_team_findings": analysis["red_team_findings"],
        "lessons_learned": analysis["lessons_learned"]
    }
