"""Evidence-driven executive report assembly (Pillars 01/02).

Every field in the generated executive report is derived from real pipeline
outputs — consensus results, stochastic simulation stats, agent findings, and
retrieved memory evidence — NEVER from hardcoded invented operational facts.
Where a field cannot be sourced it is explicitly marked as requiring human
verification instead of being invented.
"""
import datetime
from typing import Dict, Any, List, Optional


def _sim_plan(simulations: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not simulations:
        return None
    first: Optional[Dict[str, Any]] = None
    for s in simulations:
        if isinstance(s, dict):
            if s.get("recommended"):
                return s
            if first is None:
                first = s
    return first


def assemble_evidence_ledger(
    consensus: Dict[str, Any],
    simulations: List[Dict[str, Any]],
    agent_findings: List[Dict[str, Any]],
    evidence: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Collapses real pipeline outputs into a verifiable evidence ledger."""
    ledger: Dict[str, Any] = {"consensus": {}, "simulation": {}, "agent_findings": [], "memory_evidence": [], "empty": True}

    # Consensus facts (from live deliberation / dynamic parametric engine)
    consensus = consensus if isinstance(consensus, dict) else {}
    consensus_score = consensus.get("consensus_score")
    ledger["consensus"] = {
        "selected_strategy": consensus.get("selected_strategy"),
        "consensus_score": round(float(consensus_score), 3) if isinstance(consensus_score, (int, float)) else None,
        "provider": consensus.get("provider") or "unknown",
        "supporting_agents": consensus.get("supporting_agents") or [],
        "dissenting_agents": consensus.get("dissenting_agents") or [],
        "reasoning_summary": consensus.get("reasoning_summary"),
        "deliberation_stages": consensus.get("messages_count"),
    }

    # Simulation facts (real stochastic Monte-Carlo outputs)
    plan = _sim_plan(simulations or [])
    if plan:
        plan = plan if isinstance(plan, dict) else {}
    if plan:
        ledger["simulation"] = {
            "plan_id": plan.get("id"),
            "title": plan.get("title"),
            "success_likelihood": plan.get("success_likelihood"),
            "risk_score": plan.get("risk_score"),
            "median_time_mins": plan.get("estimated_time_mins"),
            "cost_usd": plan.get("cost_usd"),
            "confidence_interval": plan.get("ci"),
            "variance": plan.get("variance"),
            "iterations_run": plan.get("iterations_run"),
            "methodology": plan.get("methodology"),
            "explanation": plan.get("explanation"),
            "pros": plan.get("pros") or [],
            "cons": plan.get("cons") or [],
        }

    # Agent findings (real delivered outputs, with provenance labels)
    findings = []
    for f in (agent_findings or []):
        if not isinstance(f, dict):
            continue  # no usable evidence in a null/primitive result
        findings.append({
            "agent": f.get("executed_by") or f.get("agent_name") or f.get("agent_id"),
            "task": f.get("task_name"),
            "deliverable": str(f.get("deliverable") or f.get("reasoning_trace") or "")[:300],
            "framework": f.get("framework"),
            "simulated": bool(f.get("simulated")),
            "evidence_refs": f.get("evidence_refs") or [],
        })
    ledger["agent_findings"] = findings

    # Memory evidence (retrieved Qdrant passages, provenance-labeled)
    memory_refs: List[Dict[str, Any]] = []
    raw = (evidence or {}).get("memory_refs") or []
    raw = [r for r in raw if isinstance(r, dict)]
    seen = set()
    for r in sorted(raw, key=lambda x: float(x.get("similarity_score") or 0.0), reverse=True):
        mid = r.get("memory_id") or r.get("ref_id")
        if mid and mid in seen:
            continue
        if mid:
            seen.add(mid)
        memory_refs.append({
            "memory_id": mid,
            "collection": r.get("collection") or r.get("memory_type"),
            "title": r.get("title") or "",
            "content": str(r.get("content") or "")[:220],
            "similarity_score": r.get("similarity_score"),
            "is_synthetic": bool(r.get("is_synthetic")),
            "source": r.get("source") or "retrieval",
        })
    ledger["memory_evidence"] = memory_refs
    ledger["empty"] = not (ledger["agent_findings"] or ledger["memory_evidence"] or ledger["simulation"])
    return ledger


def assemble_executive_report(
    situation: str,
    consensus: Dict[str, Any],
    selected_strategy: str,
    simulations: List[Dict[str, Any]],
    agent_findings: List[Dict[str, Any]],
    evidence: Optional[Dict[str, Any]],
    profile: Dict[str, Any],
) -> Dict[str, Any]:
    """Builds a provenance-enforced Domain Command Report from the evidence ledger."""
    ledger = assemble_evidence_ledger(consensus, simulations, agent_findings, evidence)
    sim = ledger["simulation"]
    con = ledger["consensus"]

    confidence = con.get("consensus_score")
    confidence_str = f"{int(confidence * 100)}%" if confidence is not None else "N/A (no consensus recorded)"

    recovery_str = "Not estimated"
    if sim:
        t = sim.get("median_time_mins")
        recovery_str = f"Simulation-estimated {t} min median ({sim.get('methodology')})" if t is not None else sim.get("methodology") or "Not estimated"

    # Immediate actions derived ONLY from real agent findings/simulation plan.
    immediate_actions: List[str] = []
    for f in ledger["agent_findings"][:3]:
        if f.get("deliverable"):
            label = "SIMULATED" if f.get("simulated") else "LIVE"
            immediate_actions.append(f"{label} [{f.get('agent')}]: {f.get('deliverable')[:120]}")
    if not immediate_actions and sim:
        immediate_actions.append(f"{sim.get('plan_id')} ({sim.get('methodology')}): {str(sim.get('explanation') or '')[:160]}")
    if not immediate_actions:
        immediate_actions.append("Awaiting validated agent findings — no verified action is specified in this run.")

    # Key evidence from retrieved memory (attributable).
    key_evidence: List[str] = []
    for m in ledger["memory_evidence"][:4]:
        kind = "SYNTHETIC-DEMO" if m.get("is_synthetic") else "RETRIEVED"
        sim_txt = f"{m.get('title')} [{m.get('collection')}, similarity {m.get('similarity_score')}] ({kind}, source={m.get('source')})"
        key_evidence.append(sim_txt)
    if not key_evidence:
        key_evidence.append("No verified evidence was retrieved for this mission.")

    probable_causes: List[str] = []
    for f in ledger["agent_findings"]:
        t = str(f.get("deliverable") or "")
        if t and any(k in t.lower() for k in ("cause", "root", "fail", "degrad", "anomal", "error", "outage")):
            probable_causes.append(f"{f.get('agent')}: {t[:140]}")
    if not probable_causes:
        probable_causes.append("Root-cause analysis pending — no verified evidence in this run.")

    risk_register: List[Dict[str, Any]] = []
    if sim:
        risk_register.append({
            "risk": f"Residual risk of {sim.get('plan_id')}",
            "impact": ("HIGH" if (sim.get("risk_score") or 0) >= 0.5 else "MEDIUM" if (sim.get("risk_score") or 0) >= 0.25 else "LOW"),
            "value": sim.get("risk_score"),
            "mitigation": str(sim.get("explanation") or "No mitigation recorded."),
            "source": f"{sim.get('methodology')} — estimate, not a live measurement",
        })
    if not risk_register:
        risk_register.append({"risk": "Unassessed", "impact": "UNKNOWN", "mitigation": "Requires live adversarial run.", "source": "not measured"})

    operational_plan: List[str] = []
    if sim:
        operational_plan.append(f"Phase 1 — Contain: {str(sim.get('explanation') or '')[:150]}")
        for p in (sim.get("pros") or [])[:2]:
            operational_plan.append(f"Expected benefit ({sim.get('plan_id')}): {p}")
    if not operational_plan:
        operational_plan.append("Operational sequencing requires live runbook data; none supplied in this run.")

    unverified_fields = [
        "stakeholders", "communication_plan.details", "contingency_plan", "lessons_learned", "red_team_findings"
    ]

    report = {
        "title": profile.get("title", "AUTONOMOUS CRISIS RESPONSE REPORT"),
        "crisis_title": profile.get("title", "AUTONOMOUS CRISIS RESPONSE REPORT"),
        "domain": profile.get("domain"),
        "severity": profile.get("severity", "CRITICAL INCIDENT (per domain pack)"),
        "situation": situation,
        "stakeholders_affected": ["Pending validated stakeholder identification - requires live affected-surface data."],
        "recommended_strategy": f"{selected_strategy or 'N/A'} — consensus {confidence_str} via {con.get('provider') or 'unknown'}",
        "estimated_recovery": recovery_str,
        "confidence": confidence_str,
        "human_approval_required": True,
        "approval_notice": "Autonomous system produced this brief from pipeline evidence. Destructive or high-impact actions require human commander sign-off.",
        "why_this_strategy": con.get("reasoning_summary") or "No consensus reasoning recorded in this run.",
        "probable_causes": probable_causes,
        "key_evidence": key_evidence,
        "immediate_actions": immediate_actions,
        "operational_plan": operational_plan,
        "communication_plan": {
            "status": "PENDING_HUMAN_VALIDATION",
            "public_statement": "Draft statement — operational figures are not yet verified and must not be published as fact.",
        },
        "risk_register": risk_register,
        "contingency_plan": "Requires operator-defined contingency data; none was supplied in this run.",
        "dissenting_opinions": con.get("dissenting_agents") or ["No dissent recorded in this run."],
        "red_team_findings": [
            "Red-team audit produced estimates only; residual risk is unverified without a live adversarial run."
        ],
        "verification_checklist": [
            "Confirm incident scope against live telemetry",
            "Validate recommended plan risk figures with an operator",
            "Approve communication statement before any external send",
            "Record post-action outcome for memory ingestion",
        ],
        "lessons_learned": [
            f"Evidence ledger registered {len(ledger['memory_evidence'])} memory references, "
            f"{len(ledger['agent_findings'])} agent finding(s), {1 if sim else 0} simulation result(s)."
        ],
        "evidence_sources": ledger,
        "fabrication_policy": {
            "policy": "ENFORCE_PROVENANCE",
            "no_invented_claims": True,
            "unverified_fields": unverified_fields,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        },
    }
    return report