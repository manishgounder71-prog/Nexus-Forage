import uuid
import datetime
from typing import Dict, Any, List
from app.schemas.agent_schemas import AgentMessageSchema

class InterAgentCommunicator:
    def __init__(self):
        self.message_store: List[AgentMessageSchema] = []

    def send_message(
        self,
        from_agent: str,
        to_agent: str,
        mission_id: str,
        message_type: str,  # REQUEST, RESPONSE, EVIDENCE, PROPOSAL, CHALLENGE, AGREEMENT, DISAGREEMENT, DECISION
        content: Dict[str, Any],
        confidence: float = 0.9
    ) -> AgentMessageSchema:
        msg = AgentMessageSchema(
            message_id=str(uuid.uuid4()),
            from_agent=from_agent,
            to_agent=to_agent,
            mission_id=mission_id,
            message_type=message_type,
            content=content,
            confidence=confidence,
            timestamp=datetime.datetime.utcnow().isoformat()
        )
        self.message_store.append(msg)
        return msg

    def get_mission_messages(self, mission_id: str) -> List[AgentMessageSchema]:
        return [m for m in self.message_store if m.mission_id == mission_id]

communicator = InterAgentCommunicator()
