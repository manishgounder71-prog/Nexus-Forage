import pytest
import asyncio
from app.orchestration.dag_engine import ParallelDAGEngine

@pytest.mark.asyncio
async def test_dag_parallel_execution_no_cycles():
    dag = ParallelDAGEngine()
    n1 = dag.add_task("Task 1", "intel_01", "Incident Analyst Agent")
    n2 = dag.add_task("Task 2", "risk_01", "Risk Strategist Agent")
    n3 = dag.add_task("Task 3", "strategist_01", "Response Strategist Agent")

    dag.add_dependency(n1.task_id, n3.task_id)
    dag.add_dependency(n2.task_id, n3.task_id)

    assert not dag.validate_has_cycles()

    async def mock_runner(node):
        return {"status": "SUCCESS", "task": node.name}

    results = await dag.execute_dag(mock_runner)
    assert results["completed_tasks"] == 3
    assert results["total_tasks"] == 3

def test_dag_cycle_detection():
    dag = ParallelDAGEngine()
    n1 = dag.add_task("Task A", "agent_1", "Agent A")
    n2 = dag.add_task("Task B", "agent_2", "Agent B")

    # Create cycle A -> B -> A
    dag.add_dependency(n1.task_id, n2.task_id)
    dag.add_dependency(n2.task_id, n1.task_id)

    assert dag.validate_has_cycles() is True
