import asyncio
import uuid
import datetime
from typing import Dict, List, Set, Any, Optional

class DAGNode:
    def __init__(self, task_id: str, name: str, agent_id: str, agent_name: str):
        self.task_id = task_id
        self.name = name
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.state = "PENDING"  # PENDING, READY, RUNNING, COMPLETED, FAILED, BLOCKED
        self.dependencies: Set[str] = set()
        self.dependents: Set[str] = set()
        self.result: Optional[Dict[str, Any]] = None

class ParallelDAGEngine:
    def __init__(self):
        self.nodes: Dict[str, DAGNode] = {}

    def add_task(self, name: str, agent_id: str, agent_name: str, task_id: Optional[str] = None) -> DAGNode:
        tid = task_id or str(uuid.uuid4())
        node = DAGNode(task_id=tid, name=name, agent_id=agent_id, agent_name=agent_name)
        self.nodes[tid] = node
        return node

    def add_dependency(self, parent_task_id: str, child_task_id: str):
        if parent_task_id in self.nodes and child_task_id in self.nodes:
            self.nodes[child_task_id].dependencies.add(parent_task_id)
            self.nodes[parent_task_id].dependents.add(child_task_id)

    def validate_has_cycles(self) -> bool:
        """Cycle detection using DFS state tracking."""
        visited = set()
        rec_stack = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            for dep_id in self.nodes[node_id].dependents:
                if dep_id not in visited:
                    if dfs(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True

            rec_stack.remove(node_id)
            return False

        for nid in self.nodes:
            if nid not in visited:
                if dfs(nid):
                    return True
        return False

    async def execute_dag(self, agent_runner_func, event_callback_func=None) -> Dict[str, Any]:
        """
        Executes independent ready tasks concurrently in parallel.
        Notifies state transition events.
        """
        if self.validate_has_cycles():
            raise ValueError("[DAGEngine] Cyclic dependency detected in DAG graph!")

        completed_tasks: Set[str] = set()

        while len(completed_tasks) < len(self.nodes):
            # Find tasks whose dependencies are all completed and state is PENDING
            ready_nodes = []
            for nid, node in self.nodes.items():
                if node.state == "PENDING" and node.dependencies.issubset(completed_tasks):
                    node.state = "READY"
                    ready_nodes.append(node)

            if not ready_nodes and len(completed_tasks) < len(self.nodes):
                # Deadlock / Blocked state
                for nid, node in self.nodes.items():
                    if node.state not in ("COMPLETED", "FAILED"):
                        node.state = "BLOCKED"
                break

            # Execute all ready nodes concurrently
            async def run_single_node(node: DAGNode):
                node.state = "RUNNING"
                if event_callback_func:
                    await event_callback_func("TASK_STARTED", node)

                try:
                    res = await agent_runner_func(node)
                    node.result = res
                    node.state = "COMPLETED"
                    completed_tasks.add(node.task_id)
                    if event_callback_func:
                        await event_callback_func("TASK_COMPLETED", node)
                except Exception as e:
                    node.state = "FAILED"
                    node.result = {"error": str(e)}
                    if event_callback_func:
                        await event_callback_func("TASK_FAILED", node)

            await asyncio.gather(*[run_single_node(n) for n in ready_nodes])

        return {
            "total_tasks": len(self.nodes),
            "completed_tasks": len(completed_tasks),
            "results": {nid: n.result for nid, n in self.nodes.items()}
        }
