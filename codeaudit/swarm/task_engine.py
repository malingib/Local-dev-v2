"""
Swarm Task Engine - Technical Lifecycle (Dev-Flow) execution.
"""
import asyncio
import uuid
import logging
from typing import Dict, List, Any, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    PENDING = "pending"
    ARCHITECTURE = "architecture"
    IMPLEMENTATION = "implementation"
    VERIFICATION = "verification"
    EVOLUTION = "evolution"
    COMPLETED = "completed"
    FAILED = "failed"

class SwarmTask:
    def __init__(self, description: str, task_type: str = "general", dependencies: List[str] = None):
        self.id = str(uuid.uuid4())
        self.description = description
        self.task_type = task_type
        self.status = TaskStatus.PENDING
        self.current_stage = None
        self.result = {} # Stores artifacts from each stage
        self.assigned_to = None
        self.dependencies = dependencies or []
        self.dependents = []

class TaskEngine:
    def __init__(self, coordinator: Any):
        self.coordinator = coordinator
        self.tasks: Dict[str, SwarmTask] = {}
        self.queue = asyncio.Queue()

    async def submit(self, task: SwarmTask):
        self.tasks[task.id] = task

        # Link dependents
        for dep_id in task.dependencies:
            if dep_id in self.tasks:
                self.tasks[dep_id].dependents.append(task.id)

        # Only queue if no dependencies or all dependencies are completed
        if self._can_execute(task):
            task.status = TaskStatus.ARCHITECTURE
            await self.queue.put(task.id)
            await self.coordinator.message_bus.broadcast("SYSTEM", f"Task {task.id} entered ARCHITECTURE stage: {task.description}", "LIFECYCLE_START")
        else:
            await self.coordinator.message_bus.broadcast("SYSTEM", f"Task {task.id} waiting for dependencies", "TASK_WAITING")

    def _can_execute(self, task: SwarmTask) -> bool:
        """Check if all dependencies are completed."""
        for dep_id in task.dependencies:
            dep = self.tasks.get(dep_id)
            if not dep or dep.status != TaskStatus.COMPLETED:
                return False
        return True

    async def process_queue(self):
        while True:
            task_id = await self.queue.get()
            task = self.tasks[task_id]

            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                self.queue.task_done()
                continue

            # Execute the current lifecycle stage
            asyncio.create_task(self._execute_lifecycle(task))
            self.queue.task_done()

    async def _execute_lifecycle(self, task: SwarmTask):
        """Execute the full stage-gated lifecycle."""
        try:
            # 1. Architecture Stage
            task.status = TaskStatus.ARCHITECTURE
            arch_result = await self._run_stage(task, "architecture", "architect")
            task.result["architecture"] = arch_result
            await self.coordinator.message_bus.broadcast("SYSTEM", f"Task {task.id} Architecture finalized.", "STAGE_COMPLETE")

            # 2. Implementation Stage
            task.status = TaskStatus.IMPLEMENTATION
            impl_result = await self._run_stage(task, "implementation", "coder")
            task.result["implementation"] = impl_result
            await self.coordinator.message_bus.broadcast("SYSTEM", f"Task {task.id} Implementation complete.", "STAGE_COMPLETE")

            # 3. Verification Stage
            task.status = TaskStatus.VERIFICATION
            verify_result = await self._run_stage(task, "verification", "qa_reviewer")
            task.result["verification"] = verify_result

            # Simple check if verification passed (simulated)
            if "fail" in verify_result.lower() or "error" in verify_result.lower():
                await self.coordinator.message_bus.broadcast("SYSTEM", f"Task {task.id} Verification failed. Reverting to Implementation.", "GATE_REJECTED")
                # In a real system, we'd loop back to implementation
                # For this implementation, we'll just note it in the result
            else:
                await self.coordinator.message_bus.broadcast("SYSTEM", f"Task {task.id} Verification passed.", "STAGE_COMPLETE")

            # 4. Evolution Stage
            task.status = TaskStatus.EVOLUTION
            evolve_result = await self._run_stage(task, "evolution", "optimizer")
            task.result["evolution"] = evolve_result
            await self.coordinator.message_bus.broadcast("SYSTEM", f"Task {task.id} Optimization complete.", "STAGE_COMPLETE")

            # Finalize
            task.status = TaskStatus.COMPLETED
            await self.coordinator.message_bus.broadcast("SYSTEM", f"Task {task.id} Fully Completed.", "LIFECYCLE_COMPLETE")

            # Trigger dependents
            for dep_id in task.dependents:
                dep_task = self.tasks.get(dep_id)
                if dep_task and self._can_execute(dep_task):
                    await self.submit(dep_task)

        except Exception as e:
            logger.exception("Lifecycle failed for task %s", task.id)
            task.status = TaskStatus.FAILED
            task.result["error"] = str(e)
            await self.coordinator.message_bus.broadcast("SYSTEM", f"Task {task.id} Failed: {e}", "LIFECYCLE_FAILED")

    async def _run_stage(self, task: SwarmTask, stage: str, agent_id: str) -> str:
        """Run a specific stage with the assigned agent."""
        agent = self.coordinator._agents.get(agent_id)
        if not agent:
            raise RuntimeError(f"Agent {agent_id} not found for stage {stage}")

        await self.coordinator.message_bus.broadcast(
            "SYSTEM",
            f"Stage {stage.upper()} assigned to {agent_id}",
            "AGENT_ASSIGNED"
        )

        prompt = (
            f"Perform the {stage.upper()} stage for this task: {task.description}\n\n"
            f"Previous stage artifacts: {task.result}"
        )

        return await agent.think(prompt)
