import pytest
import asyncio
from app.orchestration.mission_engine import master_mission_engine

@pytest.mark.asyncio
async def test_end_to_end_mission_execution():
    mission_id = "test_msn_1001"
    raw_prompt = "University examination system failed 24 hours before exams."
    
    events_log = []
    async def mock_broadcaster(event):
        events_log.append(event)

    res = await master_mission_engine.execute_mission_pipeline(
        mission_id=mission_id,
        raw_prompt=raw_prompt,
        event_broadcaster=mock_broadcaster
    )

    assert res["status"] == "COMPLETED"
    assert "PLAN_B" in res["consensus"]["selected_strategy"]
    assert res["domain"] == "UNIVERSITY_OPERATIONS"
    assert len(events_log) >= 12
    event_types = [e["event_type"] for e in events_log]
    assert "MISSION_CREATED" in event_types
    assert "DOMAIN_DETECTED" in event_types
    assert "DOMAIN_PACK_SELECTED" in event_types
    assert "ORGANIZATION_FORMED" in event_types
    assert "ORGANIZATION_ADAPTED" in event_types
    assert "MISSION_COMPLETED" in event_types
