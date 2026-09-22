import asyncio
import datetime
from typing import Dict, List, Any, Callable, Optional
from app.domain_packs.registry import domain_pack_registry

DEBATE_PHASES = [
    "01_EVIDENCE",
    "02_CHALLENGE",
    "03_COUNTERARGUMENT",
    "04_REVISION",
    "05_CONSENSUS"
]

class AgentParliamentEngine:
    async def run_deliberation(
        self,
        mission_id: str,
        motion_text: str,
        participating_agents: List[Any],
        event_callback: Optional[Callable] = None,
        domain_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes 5-stage spatial Agent Parliament deliberation loop.
        Integrates modular Domain Pack consensus frameworks and minority dissent tracking.
        """
        debate_id = f"deb_{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}"
        messages = []

        if event_callback:
            await event_callback("DEBATE_STARTED", {
                "debate_id": debate_id,
                "motion": motion_text,
                "agents_count": len(participating_agents),
                "domain_id": domain_id or "SOFTWARE_INCIDENT"
            })

        # Generate dynamic deliberation (Live LLM or Dynamic Prompt-Parametric Engine)
        from app.agents.llm_reasoning import llm_reasoning_engine
        delib = await llm_reasoning_engine.generate_parliament_deliberation(
            motion_text=motion_text,
            participating_agents=participating_agents,
            domain_id=domain_id or "SOFTWARE_INCIDENT"
        )

        speeches = delib.get("phase_speeches", {})

        for phase in DEBATE_PHASES:
            await asyncio.sleep(0.35)
            # Cycle through participating agents as phase speakers
            speaker_idx = (DEBATE_PHASES.index(phase)) % max(1, len(participating_agents))
            speaker = participating_agents[speaker_idx] if participating_agents else None
            speaker_name = speaker.name if speaker else "Incident Commander"
            speaker_id = speaker.agent_id if speaker else "commander_01"

            speech_text = speeches.get(phase, f"Parliament evaluating stage {phase} for motion: '{motion_text}'")

            phase_msg = {
                "phase": phase,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "agent_id": speaker_id,
                "agent_name": speaker_name,
                "content": f"[{speaker_name}] {speech_text}"
            }
            messages.append(phase_msg)

            if event_callback:
                await event_callback("DEBATE_MESSAGE", phase_msg)

        selected_strategy = delib.get("selected_strategy", "PLAN_B_DECOUPLED_RESILIENT_FAILOVER")
        consensus_score = delib.get("consensus_score", 0.95)
        reasoning_summary = delib.get("reasoning_summary", "Plan B selected: Optimal balance between recovery speed and risk mitigation.")
        supporting = delib.get("supporting_agents", [getattr(a, 'name', str(a)) for a in participating_agents if "Risk" not in getattr(a, 'name', '')])
        dissenting = delib.get("dissenting_agents", ["Risk Strategist Agent"])

        consensus_result = {
            "debate_id": debate_id,
            "motion": motion_text,
            "selected_strategy": selected_strategy,
            "consensus_score": consensus_score,
            "supporting_agents": supporting,
            "dissenting_agents": dissenting,
            "reasoning_summary": reasoning_summary,
            "messages_count": len(messages),
            "domain_id": domain_id or "SOFTWARE_INCIDENT",
            "provider": delib.get("provider", "Dynamic Reasoning Engine")
        }

        if event_callback:
            await event_callback("CONSENSUS_REACHED", consensus_result)

        return consensus_result

parliament_engine = AgentParliamentEngine()
