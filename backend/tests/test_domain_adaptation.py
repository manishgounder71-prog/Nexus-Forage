import pytest
from app.domain_packs.detector import domain_detector
from app.domain_packs.registry import domain_pack_registry
from app.domain_packs.capability_extractor import capability_extractor
from app.orchestration.adaptive_org_engine import adaptive_org_engine
from app.orchestration.simulation_engine import simulation_engine

def test_domain_detection_all_five_domains():
    scenarios = [
        ("Production started failing immediately after the latest deployment. Rollback needed.", "SOFTWARE_INCIDENT"),
        ("Our enterprise payment gateway failed, customer billing transactions dropping.", "ENTERPRISE_CRISIS"),
        ("We have three months of runway left. Should we reduce costs, raise funding, or pivot?", "STARTUP_STRATEGY"),
        ("Our main supplier stopped deliveries and 12 cargo vessels are blocked by port strikes.", "SUPPLY_CHAIN"),
        ("The university examination portal crashed 24 hours before finals.", "UNIVERSITY_OPERATIONS")
    ]

    for prompt, expected_domain in scenarios:
        res = domain_detector.detect_domain(prompt)
        assert res["primary_domain"] == expected_domain
        assert res["confidence"] >= 0.70
        assert len(res["required_capabilities"]) >= 3

def test_hybrid_mission_detection():
    hybrid_prompt = "Our production server cluster failed, affecting customer payment checkout and causing major financial losses."
    res = domain_detector.detect_domain(hybrid_prompt)
    assert res["primary_domain"] in ["SOFTWARE_INCIDENT", "ENTERPRISE_CRISIS"]
    assert res["is_hybrid"] is True
    assert len(res["secondary_domains"]) >= 1

def test_domain_pack_registry():
    packs = domain_pack_registry.list_packs()
    assert len(packs) == 5
    domain_ids = [p["domain_id"] for p in packs]
    assert "SOFTWARE_INCIDENT" in domain_ids
    assert "ENTERPRISE_CRISIS" in domain_ids
    assert "STARTUP_STRATEGY" in domain_ids
    assert "SUPPLY_CHAIN" in domain_ids
    assert "UNIVERSITY_OPERATIONS" in domain_ids

    scenarios = domain_pack_registry.get_all_sample_scenarios()
    assert len(scenarios) >= 5

def test_adaptive_org_formation():
    pack = domain_pack_registry.get_pack("SOFTWARE_INCIDENT")
    caps = ["root_cause_analysis", "infrastructure_analysis", "rollback_planning"]
    team = adaptive_org_engine.form_organization(caps, pack)
    assert len(team) >= 3
    team_names = [t.agent_name for t in team]
    assert "Mission Commander" in team_names
    assert any("Root Cause" in name or "Rollback" in name for name in team_names)

def test_simulation_engine_domain_strategies():
    strategies = simulation_engine.simulate_strategies(domain_id="SUPPLY_CHAIN")
    assert len(strategies) == 3
    assert any(s["recommended"] for s in strategies)
