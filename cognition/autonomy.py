"""
Autonomy Controller — enables the agent to independently plan,
execute multi-step tasks, track progress, and make decisions.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Task:
    id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
    subtasks: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    result: str | None = None
    error: str | None = None
    created: str = ""
    started: str | None = None
    completed: str | None = None
    max_retries: int = 3
    retries: int = 0

    def __post_init__(self) -> None:
        if not self.created:
            self.created = datetime.now().isoformat()


class AutonomyController:
    """
    Enables independent task planning, execution, and decision-making.
    The agent can decompose goals into tasks, prioritize, execute, and adapt.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._execution_log: list[dict[str, Any]] = []
        self._decision_history: list[dict[str, Any]] = []
        self._active_plan: str | None = None

    def create_plan(self, goal: str, steps: list[str]) -> str:
        """Create an execution plan from a goal and steps."""
        plan_id = str(uuid.uuid4())[:8]
        self._active_plan = plan_id

        parent_task = Task(
            id=plan_id,
            title=f"Plan: {goal}",
            description=f"Execute plan for: {goal}",
            priority=Priority.HIGH,
        )
        self._tasks[plan_id] = parent_task

        for i, step in enumerate(steps):
            task_id = f"{plan_id}-{i + 1}"
            task = Task(
                id=task_id,
                title=step,
                description=step,
                dependencies=[f"{plan_id}-{i}" if i > 0 else plan_id],
            )
            self._tasks[task_id] = task
            parent_task.subtasks.append(task_id)

        self._log("plan_created", {"plan_id": plan_id, "goal": goal, "steps": len(steps)})
        return plan_id

    def get_next_tasks(self, limit: int = 5) -> list[Task]:
        """Get the next tasks ready for execution (no blocked dependencies)."""
        ready: list[Task] = []

        for task in self._tasks.values():
            if task.status != TaskStatus.PENDING:
                continue

            deps_met = all(
                self._tasks.get(dep, Task(id="", title="", description="")).status == TaskStatus.COMPLETED
                for dep in task.dependencies
            )

            if deps_met:
                ready.append(task)

        ready.sort(key=lambda t: t.priority.value, reverse=True)
        return ready[:limit]

    def start_task(self, task_id: str) -> Task | None:
        """Mark a task as in-progress."""
        task = self._tasks.get(task_id)
        if task:
            task.status = TaskStatus.IN_PROGRESS
            task.started = datetime.now().isoformat()
            self._log("task_started", {"task_id": task_id, "title": task.title})
        return task

    def complete_task(self, task_id: str, result: str) -> Task | None:
        """Mark a task as completed with result."""
        task = self._tasks.get(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed = datetime.now().isoformat()
            self._log("task_completed", {"task_id": task_id, "result_length": len(result)})
        return task

    def fail_task(self, task_id: str, error: str) -> Task | None:
        """Mark a task as failed. Auto-retry if retries remain."""
        task = self._tasks.get(task_id)
        if task:
            task.retries += 1
            if task.retries < task.max_retries:
                task.status = TaskStatus.PENDING
                task.error = error
                self._log("task_retried", {"task_id": task_id, "retry": task.retries, "error": error})
            else:
                task.status = TaskStatus.FAILED
                task.error = error
                self._log("task_failed", {"task_id": task_id, "error": error})
        return task

    def cancel_task(self, task_id: str) -> Task | None:
        """Cancel a task."""
        task = self._tasks.get(task_id)
        if task:
            task.status = TaskStatus.CANCELLED
            self._log("task_cancelled", {"task_id": task_id})
        return task

    def decide(
        self, question: str, options: list[str], criteria: dict[str, float] | None = None
    ) -> dict[str, Any]:
        """Make a decision between multiple options using weighted criteria."""
        if not criteria:
            criteria = {"relevance": 0.3, "feasibility": 0.3, "impact": 0.4}

        scores: dict[str, float] = {}
        for option in options:
            score = 0.0
            for criterion, weight in criteria.items():
                score += weight * 0.7  # placeholder scoring
            scores[option] = round(score, 3)

        best_option = max(scores, key=scores.get)

        decision = {
            "question": question,
            "options": options,
            "criteria": criteria,
            "scores": scores,
            "chosen": best_option,
            "reasoning": f"Selected '{best_option}' based on weighted criteria: {', '.join(criteria.keys())}",
            "timestamp": datetime.now().isoformat(),
        }

        self._decision_history.append(decision)
        self._log("decision_made", decision)
        return decision

    def get_progress(self) -> dict[str, Any]:
        """Get overall progress of the active plan."""
        status_counts = {s.value: 0 for s in TaskStatus}
        total_priority = 0

        for task in self._tasks.values():
            status_counts[task.status.value] += 1
            total_priority += task.priority.value

        total = len(self._tasks)
        completed = status_counts["completed"]
        progress_pct = (completed / total * 100) if total > 0 else 0

        return {
            "plan_id": self._active_plan,
            "total_tasks": total,
            "completed": completed,
            "in_progress": status_counts["in_progress"],
            "pending": status_counts["pending"],
            "failed": status_counts["failed"],
            "blocked": status_counts["blocked"],
            "progress_percent": round(progress_pct, 1),
            "average_priority": round(total_priority / total, 1) if total > 0 else 0,
        }

    def adapt_plan(self, reason: str, new_steps: list[str] | None = None) -> str:
        """Adapt the plan based on new information or failures."""
        adaptation = {
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "previous_progress": self.get_progress(),
        }

        failed_tasks = [
            t for t in self._tasks.values() if t.status == TaskStatus.FAILED
        ]

        for task in failed_tasks:
            task.status = TaskStatus.CANCELLED
            adaptation[f"cancelled_{task.id}"] = task.title

        if new_steps and self._active_plan:
            for i, step in enumerate(new_steps):
                task_id = f"{self._active_plan}-new-{i + 1}"
                task = Task(
                    id=task_id,
                    title=step,
                    description=step,
                    priority=Priority.HIGH,
                )
                self._tasks[task_id] = task

        self._log("plan_adapted", adaptation)
        return f"Plan adapted: {reason}. {len(new_steps or [])} new steps added."

    def summarize(self) -> str:
        """Generate a human-readable summary of execution status."""
        progress = self.get_progress()
        lines = [
            f"=== Execution Summary ===",
            f"Plan: {self._active_plan or 'None active'}",
            f"Progress: {progress['progress_percent']}% ({progress['completed']}/{progress['total_tasks']})",
            f"Status: {progress['in_progress']} active, {progress['pending']} pending, {progress['failed']} failed",
            "",
        ]

        for task in self._tasks.values():
            icon = {
                TaskStatus.PENDING: "[ ]",
                TaskStatus.IN_PROGRESS: "[>]",
                TaskStatus.COMPLETED: "[x]",
                TaskStatus.FAILED: "[!]",
                TaskStatus.BLOCKED: "[B]",
                TaskStatus.CANCELLED: "[-]",
            }.get(task.status, "[?]")
            lines.append(f"  {icon} {task.title}")

        return "\n".join(lines)

    def _log(self, event: str, data: dict[str, Any]) -> None:
        self._execution_log.append({
            "event": event,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        })

    def get_execution_log(self) -> list[dict[str, Any]]:
        return self._execution_log.copy()

    def get_decision_history(self) -> list[dict[str, Any]]:
        return self._decision_history.copy()
