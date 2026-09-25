"""
Sub-Agent System — spawn, manage, and orchestrate child agents
for parallel task execution and deep work.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class AgentState(Enum):
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


class AgentRole(Enum):
    RESEARCHER = "researcher"
    CODER = "coder"
    ANALYZER = "analyzer"
    WRITER = "writer"
    REVIEWER = "reviewer"
    COORDINATOR = "coordinator"
    CUSTOM = "custom"


@dataclass
class AgentTask:
    id: str
    description: str
    status: str = "pending"
    result: str = ""
    started: str = ""
    completed: str = ""
    error: str = ""


@dataclass
class SubAgent:
    id: str
    name: str
    role: AgentRole
    state: AgentState = AgentState.IDLE
    parent_id: str | None = None
    capabilities: list[str] = field(default_factory=list)
    tasks: list[AgentTask] = field(default_factory=list)
    created: str = ""
    last_active: str = ""
    result: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.created:
            self.created = datetime.now().isoformat()
        if not self.id:
            self.id = str(uuid.uuid4())[:12]

    def assign_task(self, description: str) -> AgentTask:
        task = AgentTask(
            id=f"{self.id}-{len(self.tasks)+1}",
            description=description,
            started=datetime.now().isoformat(),
        )
        self.tasks.append(task)
        self.state = AgentState.WORKING
        self.last_active = datetime.now().isoformat()
        return task

    def complete_task(self, task_id: str, result: str) -> None:
        for task in self.tasks:
            if task.id == task_id:
                task.status = "completed"
                task.result = result
                task.completed = datetime.now().isoformat()
                break
        self.state = AgentState.COMPLETED
        self.result = result
        self.last_active = datetime.now().isoformat()

    def fail_task(self, task_id: str, error: str) -> None:
        for task in self.tasks:
            if task.id == task_id:
                task.status = "failed"
                task.error = error
                task.completed = datetime.now().isoformat()
                break
        self.state = AgentState.FAILED
        self.last_active = datetime.now().isoformat()

    def get_status(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value,
            "state": self.state.value,
            "tasks_completed": sum(1 for t in self.tasks if t.status == "completed"),
            "tasks_failed": sum(1 for t in self.tasks if t.status == "failed"),
            "tasks_pending": sum(1 for t in self.tasks if t.status == "pending"),
            "created": self.created,
            "last_active": self.last_active,
        }


class AgentOrchestrator:
    """Manages a fleet of sub-agents for parallel task execution."""

    def __init__(self, max_agents: int = 5) -> None:
        self.max_agents = max_agents
        self._agents: dict[str, SubAgent] = {}
        self._task_queue: list[dict[str, Any]] = []
        self._execution_log: list[dict[str, Any]] = []

    def spawn_agent(
        self,
        name: str,
        role: AgentRole = AgentRole.CUSTOM,
        capabilities: list[str] | None = None,
        parent_id: str | None = None,
    ) -> SubAgent:
        """Spawn a new sub-agent."""
        if len(self._agents) >= self.max_agents:
            raise RuntimeError(f"Maximum agent limit ({self.max_agents}) reached. Terminate idle agents first.")

        agent = SubAgent(
            id=str(uuid.uuid4())[:12],
            name=name,
            role=role,
            parent_id=parent_id,
            capabilities=capabilities or [],
        )
        self._agents[agent.id] = agent
        self._log("agent_spawned", {"id": agent.id, "name": name, "role": role.value})
        return agent

    def spawn_research_team(self, topic: str) -> list[SubAgent]:
        """Spawn a team of specialized research agents."""
        team = []

        coordinator = self.spawn_agent(
            name=f"Coordinator-{topic[:20]}",
            role=AgentRole.COORDINATOR,
            capabilities=["planning", "coordination", "synthesis"],
        )
        team.append(coordinator)

        researcher = self.spawn_agent(
            name=f"Researcher-{topic[:20]}",
            role=AgentRole.RESEARCHER,
            capabilities=["web_search", "fetch_url", "deep_research"],
            parent_id=coordinator.id,
        )
        team.append(researcher)

        analyzer = self.spawn_agent(
            name=f"Analyzer-{topic[:20]}",
            role=AgentRole.ANALYZER,
            capabilities=["data_analyze", "pattern_detect", "reason"],
            parent_id=coordinator.id,
        )
        team.append(analyzer)

        writer = self.spawn_agent(
            name=f"Writer-{topic[:20]}",
            role=AgentRole.WRITER,
            capabilities=["content_create", "creative_idea"],
            parent_id=coordinator.id,
        )
        team.append(writer)

        reviewer = self.spawn_agent(
            name=f"Reviewer-{topic[:20]}",
            role=AgentRole.REVIEWER,
            capabilities=["verify", "security_audit", "code_analyze"],
            parent_id=coordinator.id,
        )
        team.append(reviewer)

        self._log("research_team_spawned", {"topic": topic, "team_size": len(team)})
        return team

    def spawn_coding_team(self, project: str) -> list[SubAgent]:
        """Spawn a team for software development tasks."""
        team = []

        lead = self.spawn_agent(
            name=f"TechLead-{project[:20]}",
            role=AgentRole.COORDINATOR,
            capabilities=["planning", "architecture", "reason"],
        )
        team.append(lead)

        backend = self.spawn_agent(
            name=f"Backend-{project[:20]}",
            role=AgentRole.CODER,
            capabilities=["run_python", "code_generate", "code_analyze"],
            parent_id=lead.id,
        )
        team.append(backend)

        frontend = self.spawn_agent(
            name=f"Frontend-{project[:20]}",
            role=AgentRole.CODER,
            capabilities=["code_generate", "code_analyze"],
            parent_id=lead.id,
        )
        team.append(frontend)

        tester = self.spawn_agent(
            name=f"Tester-{project[:20]}",
            role=AgentRole.REVIEWER,
            capabilities=["run_python", "security_audit", "code_analyze"],
            parent_id=lead.id,
        )
        team.append(tester)

        self._log("coding_team_spawned", {"project": project, "team_size": len(team)})
        return team

    def delegate_task(self, agent_id: str, task_description: str) -> AgentTask | None:
        """Delegate a task to a specific agent."""
        agent = self._agents.get(agent_id)
        if not agent:
            return None
        task = agent.assign_task(task_description)
        self._log("task_delegated", {"agent_id": agent_id, "task_id": task.id, "description": task_description[:100]})
        return task

    def complete_task(self, agent_id: str, task_id: str, result: str) -> None:
        agent = self._agents.get(agent_id)
        if agent:
            agent.complete_task(task_id, result)
            self._log("task_completed", {"agent_id": agent_id, "task_id": task_id})

    def fail_task(self, agent_id: str, task_id: str, error: str) -> None:
        agent = self._agents.get(agent_id)
        if agent:
            agent.fail_task(task_id, error)
            self._log("task_failed", {"agent_id": agent_id, "task_id": task_id, "error": error})

    def terminate_agent(self, agent_id: str) -> bool:
        agent = self._agents.get(agent_id)
        if agent:
            agent.state = AgentState.TERMINATED
            agent.last_active = datetime.now().isoformat()
            self._log("agent_terminated", {"agent_id": agent_id})
            return True
        return False

    def get_agent(self, agent_id: str) -> SubAgent | None:
        return self._agents.get(agent_id)

    def list_agents(self) -> list[dict[str, Any]]:
        return [a.get_status() for a in self._agents.values()]

    def get_fleet_status(self) -> dict[str, Any]:
        states = {s.value: 0 for s in AgentState}
        for agent in self._agents.values():
            states[agent.state.value] += 1

        total_tasks = sum(len(a.tasks) for a in self._agents.values())
        completed_tasks = sum(
            sum(1 for t in a.tasks if t.status == "completed")
            for a in self._agents.values()
        )

        return {
            "total_agents": len(self._agents),
            "max_agents": self.max_agents,
            "states": states,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "utilization": completed_tasks / max(total_tasks, 1) * 100,
        }

    def get_results_summary(self) -> str:
        lines = ["=== Fleet Status ===\n"]
        for agent in self._agents.values():
            status = agent.get_status()
            icon = {
                AgentState.IDLE: "💤",
                AgentState.WORKING: "⚡",
                AgentState.COMPLETED: "✅",
                AgentState.FAILED: "❌",
                AgentState.TERMINATED: "🛑",
            }.get(agent.state, "❓")
            lines.append(
                f"{icon} [{agent.role.value:12}] {agent.name:30} | "
                f"Tasks: {status['tasks_completed']}✅ {status['tasks_failed']}❌ {status['tasks_pending']}⏳"
            )
            if agent.result:
                lines.append(f"   Result: {agent.result[:100]}")

        fleet = self.get_fleet_status()
        lines.extend([
            "",
            f"Fleet: {fleet['total_agents']}/{fleet['max_agents']} agents | "
            f"Tasks: {fleet['completed_tasks']}/{fleet['total_tasks']} completed | "
            f"Utilization: {fleet['utilization']:.0f}%",
        ])

        return "\n".join(lines)

    def _log(self, event: str, data: dict[str, Any]) -> None:
        self._execution_log.append({
            "event": event,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        })

    def get_execution_log(self) -> list[dict[str, Any]]:
        return self._execution_log.copy()
