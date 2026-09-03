import pytest
from app.agents.llm_reasoning import llm_reasoning_engine
from app.orchestration.debate_engine import parliament_engine

class MockAgent:
    def __init__(self, name, agent_id):
        self.name = name
        self.agent_id = agent_id

@pytest.mark.asyncio
async def test_dynamic_deliberation_adapts_to_novel_prompts():
    """
    Verifies that novel prompts produce dynamically differentiated strategies,
    entities, and debate messages rather than identical canned domain templates.
    """
    agents = [
        MockAgent("Incident Commander", "cmd_01"),
        MockAgent("Risk Strategist Agent", "risk_01"),
        MockAgent("Systems Architect", "arch_01")
    ]

    prompt_a = "Metropolitan water filtration telemetry compromised by ransomware in district 4"
    prompt_b = "Autonomous shipping container cranes experiencing PLC buffer overflow in Singapore"

    delib_a = await llm_reasoning_engine.generate_parliament_deliberation(prompt_a, agents)
    delib_b = await llm_reasoning_engine.generate_parliament_deliberation(prompt_b, agents)

    # Strategy names must dynamically reflect the unique crisis entities
    assert delib_a["selected_strategy"] != delib_b["selected_strategy"]
    assert "WATER" in delib_a["selected_strategy"] or "METROPOLITAN" in delib_a["selected_strategy"]
    assert "CONTAINER" in delib_b["selected_strategy"] or "SINGAPORE" in delib_b["selected_strategy"] or "AUTONOMOUS" in delib_b["selected_strategy"]

    # Reasoning summaries must reflect the distinct prompts
    assert delib_a["reasoning_summary"] != delib_b["reasoning_summary"]
    assert "District" in delib_a["reasoning_summary"] or "water" in delib_a["reasoning_summary"].lower()
    assert "Singapore" in delib_b["reasoning_summary"] or "cranes" in delib_b["reasoning_summary"].lower() or "shipping" in delib_b["reasoning_summary"].lower()

@pytest.mark.asyncio
async def test_parliament_engine_end_to_end_deliberation():
    """Verifies the complete AgentParliamentEngine produces dynamic consensus."""
    agents = [
        MockAgent("Commander", "c1"),
        MockAgent("Risk Officer", "r1")
    ]
    res = await parliament_engine.run_deliberation(
        mission_id="msn_test_delib_99",
        motion_text="Satellite communications constellation solar flare degradation",
        participating_agents=agents
    )
    assert res is not None
    assert "selected_strategy" in res
    assert "consensus_score" in res
    assert res["consensus_score"] >= 0.90
    assert len(res["supporting_agents"]) > 0
    assert "SATELLITE" in res["selected_strategy"] or "SOLAR" in res["selected_strategy"] or "COMMUNICATIONS" in res["selected_strategy"] or "PLAN_B" in res["selected_strategy"]
