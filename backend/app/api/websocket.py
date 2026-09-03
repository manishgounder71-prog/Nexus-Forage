import asyncio
import json
from typing import Dict, List, Set, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

class WebSocketManager:
    def __init__(self):
        # Maps mission_id -> list of active WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Maps org_id -> set of WebSockets subscribed to the org event stream.
        self.org_streams: Dict[str, Set[WebSocket]] = {}

    def connect_org(self, org_id: str, websocket: WebSocket):
        self.org_streams.setdefault(org_id, set()).add(websocket)

    def disconnect_org(self, org_id: str, websocket: WebSocket):
        if org_id in self.org_streams:
            self.org_streams[org_id].discard(websocket)
            if not self.org_streams[org_id]:
                del self.org_streams[org_id]

    async def broadcast_org(self, org_id: str, event_data: Dict[str, Any]):
        targets = self.org_streams.get(org_id, set())
        if not targets:
            return
        payload = json.dumps(event_data, default=str)
        disconnected = set()
        for ws in targets:
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.add(ws)
        for ws in disconnected:
            self.disconnect_org(org_id, ws)

    async def connect(self, mission_id: str, websocket: WebSocket):
        await websocket.accept()
        if mission_id not in self.active_connections:
            self.active_connections[mission_id] = set()
        self.active_connections[mission_id].add(websocket)

    def disconnect(self, mission_id: str, websocket: WebSocket):
        if mission_id in self.active_connections:
            self.active_connections[mission_id].discard(websocket)
            if not self.active_connections[mission_id]:
                del self.active_connections[mission_id]

    async def broadcast_event(self, mission_id: str, event_data: Dict[str, Any]):
        """Broadcasts real-time event to all connected clients for mission_id."""
        targets = self.active_connections.get(mission_id, set())
        # Also broadcast to global 'all' listener
        global_targets = self.active_connections.get("all", set())
        all_targets = targets.union(global_targets)

        if not all_targets:
            return

        payload = json.dumps(event_data)
        disconnected = set()
        for ws in all_targets:
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.add(ws)

        for ws in disconnected:
            self.disconnect(mission_id, ws)

websocket_manager = WebSocketManager()
router = APIRouter(prefix="/ws", tags=["WebSocket"])

@router.websocket("/missions/{mission_id}")
async def websocket_mission_stream(websocket: WebSocket, mission_id: str):
    """
    WebSocket endpoint for real-time mission execution event streaming.
    Pushes AGENT_STARTED, TASK_COMPLETED, DEBATE_MESSAGE, CONSENSUS_REACHED, RED_TEAM_STARTED, etc.
    """
    await websocket_manager.connect(mission_id, websocket)
    try:
        # Keep connection alive & handle incoming pings
        while True:
            data = await websocket.receive_text()
            # Send ack
            await websocket.send_text(json.dumps({"status": "ACK", "received": data}))
    except WebSocketDisconnect:
        websocket_manager.disconnect(mission_id, websocket)


@router.websocket("/organizations/{org_id}/events")
async def websocket_org_event_stream(websocket: WebSocket, org_id: str):
    """
    WebSocket endpoint for the organization event stream (connector events,
    incidents, crises) broadcast in real time by the event bus.
    """
    await websocket.accept()
    from app.pipeline.event_bus import event_bus
    manager = websocket_manager
    manager.connect_org(org_id, websocket)
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)

    async def relay(item: Dict):
        try:
            queue.put_nowait(item)
        except asyncio.QueueFull:
            pass

    for topic in (f"org.{org_id}.events", f"org.{org_id}.incidents", f"org.{org_id}.crises"):
        event_bus.subscribe(topic, relay)

    async def pump():
        while True:
            item = await queue.get()
            await manager.broadcast_org(org_id, {"topic": item["topic"], **item["message"]})

    pump_task = asyncio.create_task(pump())
    try:
        while True:
            # Keep alive; client may send nothing. We just await disconnect via receive.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        pump_task.cancel()
        for topic in (f"org.{org_id}.events", f"org.{org_id}.incidents", f"org.{org_id}.crises"):
            event_bus.unsubscribe(topic, relay)
        manager.disconnect_org(org_id, websocket)
