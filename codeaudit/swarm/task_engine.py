"""
Swarm Task Engine - Windmill-inspired task-based execution.
"""
import asyncio
import uuid
from typing import Dict, List, Any, Optional, Callable
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class SwarmTask:
    def __init__(self, description: str, task_type: str = "general", dependencies: List[str] = None):
        self.id = str(uuid.uuid4())
        self.description = description
        self.task_type = task_type
        self.status = TaskStatus.PENDING
        self.result = None
        self.assigned_to = None
        self.dependencies = dependencies or []
        self.dependents = [] # Tasks that depend on this one

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
            await self.queue.put(task.id)
            await self.coordinator.message_bus.broadcast("SYSTEM", f"Task {task.id} queued: {task.description}", "TASK_QUEUED")
        else:
            await self.coordinator.message_bus.broadcast("SYSTEM", f"Task {task.id} waiting for dependencies: {task.description}", "TASK_WAITING")

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

            if task.status != TaskStatus.PENDING:
                self.queue.task_done()
                continue

            task.status = TaskStatus.RUNNING

            # Simple assignment logic: find agent by task type or default to orchestrator
            target_agent = self._find_best_agent(task)
            task.assigned_to = target_agent

            await self.coordinator.message_bus.broadcast(
                "SYSTEM",
                f"Task {task.id} assigned to {target_agent}",
                "TASK_ASSIGNED"
            )

            # Simulate execution
            asyncio.create_task(self._execute_task(task))
            self.queue.task_done()

    def _find_best_agent(self, task: SwarmTask) -> str:
        mapping = {
            "ui": "ui_designer",
            "frontend": "ui_designer",
            "bug": "debugger",
            "fix": "coder",
            "security": "qa_reviewer",
            "performance": "optimizer",
            "database": "database",
            "api": "backend"
        }
        for key, agent in mapping.items():
            if key in task.description.lower() or key in task.task_type.lower():
                return agent
        return "orchestrator"

    async def _execute_task(self, task: SwarmTask):
        agent = self.coordinator._agents.get(task.assigned_to)
        if agent:
            try:
                # In a real system, this would call the agent's specific logic
                # For now, we simulate agent "thinking"
                result = await agent.think(f"Execute task: {task.description}")
                task.result = result
                task.status = TaskStatus.COMPLETED
                await self.coordinator.message_bus.broadcast(
                    task.assigned_to,
                    f"Completed task {task.id}: {result[:100]}...",
                    "TASK_COMPLETED"
                )

                # Check dependents
                for dep_id in task.dependents:
                    dep_task = self.tasks.get(dep_id)
                    if dep_task and self._can_execute(dep_task):
                        await self.queue.put(dep_id)
                        await self.coordinator.message_bus.broadcast("SYSTEM", f"Dependency cleared. Task {dep_id} queued: {dep_task.description}", "TASK_QUEUED")

            except Exception as e:
                task.status = TaskStatus.FAILED
                task.result = str(e)
                await self.coordinator.message_bus.broadcast(
                    "SYSTEM",
                    f"Task {task.id} failed: {e}",
                    "TASK_FAILED"
                )
