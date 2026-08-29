"""CrewAI event bus → live UI state, streamed to Gradio."""

from __future__ import annotations

import traceback
from datetime import datetime
from queue import Empty, Queue
from threading import Thread
from typing import Any, Iterator

import gradio as gr
from crewai.events import (
    AgentExecutionCompletedEvent,
    AgentExecutionErrorEvent,
    AgentExecutionStartedEvent,
    CrewKickoffCompletedEvent,
    CrewKickoffFailedEvent,
    CrewKickoffStartedEvent,
    MCPToolExecutionStartedEvent,
    TaskCompletedEvent,
    TaskFailedEvent,
    TaskStartedEvent,
    ToolUsageErrorEvent,
    ToolUsageFinishedEvent,
    ToolUsageStartedEvent,
    crewai_event_bus,
)

from engineering_team.crew import EngineeringTeam
from engineering_team.tools.sandbox_tools import SANDBOX_DIR, reset_sandbox
from engineering_team.ui.components import (
    DESIGN_PLACEHOLDER,
    IDLE_HEADLINE,
    OUTPUT_PLACEHOLDER,
    SANDBOX_SKIP,
    STAGES,
    TASK_LABELS,
    clean,
    escape,
    format_inline_code,
    log_tone,
    render_files,
    render_log,
    render_pipeline,
    render_status,
    stage_key,
)

TERMINAL_KINDS = {"done", "error"}


def new_state() -> dict[str, Any]:
    return {
        "phase": "idle",
        "headline": IDLE_HEADLINE,
        "stages": {stage.key: {"status": "waiting", "action": ""} for stage in STAGES},
        "log": [],
        "design": "",
        "output": "",
        "files": [],
    }


def ui_tuple(state: dict[str, Any], button_interactive: bool) -> tuple:
    return (
        render_status(state),
        render_pipeline(state),
        render_log(state),
        state["design"] or DESIGN_PLACEHOLDER,
        state["output"] or OUTPUT_PLACEHOLDER,
        render_files(state["files"]),
        gr.update(interactive=button_interactive),
    )


def run_crew(requirements: str) -> Iterator[tuple]:
    """Kick off the engineering crew and stream live station updates to the UI."""
    requirements = (requirements or "").strip()
    state = new_state()
    if not requirements:
        state["headline"] = "Enter product requirements before running the crew."
        _log(state, "Crew", "No requirements yet — paste a brief and start the build.")
        yield ui_tuple(state, True)
        return

    state["phase"] = "running"
    state["headline"] = "Opening the build floor…"
    yield ui_tuple(state, False)

    queue: Queue = Queue()
    thread = Thread(target=_run_crew_worker, args=(requirements, queue), daemon=True)
    thread.start()

    while True:
        try:
            event = queue.get(timeout=0.25)
        except Empty:
            if not thread.is_alive():
                state["phase"] = "error"
                state["headline"] = "The build stopped without a final event."
                _log(state, "Crew", "The worker thread ended unexpectedly.")
                yield ui_tuple(state, True)
                return
            continue

        apply_event(state, event)
        finished = event["kind"] in TERMINAL_KINDS
        yield ui_tuple(state, finished)
        if finished:
            return


def apply_event(state: dict[str, Any], event: dict[str, Any]) -> None:
    handler = _HANDLERS.get(event["kind"])
    if handler:
        handler(state, event)


def _run_crew_worker(requirements: str, queue: Queue) -> None:
    try:
        _emit(queue, "sandbox")
        reset_sandbox()
        with crewai_event_bus.scoped_handlers():
            _register_build_listeners(queue)
            result = EngineeringTeam().crew().kickoff(inputs={"requirements": requirements})
        raw = getattr(result, "raw", None) or str(result)
        _emit(queue, "done", output=raw)
    except Exception as exc:
        _emit(queue, "error", error=f"{exc}\n{traceback.format_exc()}")


def _emit(queue: Queue, kind: str, **payload: Any) -> None:
    queue.put({"kind": kind, **payload})


def _register_build_listeners(queue: Queue) -> None:
    @crewai_event_bus.on(CrewKickoffStartedEvent)
    def on_crew_started(_source, event):
        _emit(queue, "crew_started", name=clean(getattr(event, "crew_name", "") or "Engineering Team"))

    @crewai_event_bus.on(CrewKickoffCompletedEvent)
    def on_crew_completed(_source, event):
        _emit(queue, "crew_completed", tokens=getattr(event, "total_tokens", 0))

    @crewai_event_bus.on(CrewKickoffFailedEvent)
    def on_crew_failed(_source, event):
        _emit(queue, "crew_failed", error=clean(getattr(event, "error", "") or "Crew failed"))

    @crewai_event_bus.on(TaskStartedEvent)
    def on_task_started(_source, event):
        _emit(queue, "task_started", role=_role_from_event(event), task=_task_label(event))

    @crewai_event_bus.on(TaskCompletedEvent)
    def on_task_completed(_source, event):
        _emit(queue, "task_completed", role=_role_from_event(event), task=_task_label(event))

    @crewai_event_bus.on(TaskFailedEvent)
    def on_task_failed(_source, event):
        _emit(
            queue,
            "task_failed",
            role=_role_from_event(event),
            task=_task_label(event),
            error=clean(getattr(event, "error", "") or "Task failed"),
        )

    @crewai_event_bus.on(AgentExecutionStartedEvent)
    def on_agent_started(_source, event):
        _emit(queue, "agent_started", role=_role_from_event(event), task=_task_label(event))

    @crewai_event_bus.on(AgentExecutionCompletedEvent)
    def on_agent_completed(_source, event):
        _emit(queue, "agent_completed", role=_role_from_event(event), task=_task_label(event))

    @crewai_event_bus.on(AgentExecutionErrorEvent)
    def on_agent_error(_source, event):
        _emit(
            queue,
            "agent_error",
            role=_role_from_event(event),
            error=clean(getattr(event, "error", "") or "Agent error"),
        )

    @crewai_event_bus.on(ToolUsageStartedEvent)
    def on_tool_started(_source, event):
        _emit(
            queue,
            "tool_started",
            role=_role_from_event(event),
            message=_tool_message(event),
            filename=_tool_filename(getattr(event, "tool_args", None)),
        )

    @crewai_event_bus.on(ToolUsageFinishedEvent)
    def on_tool_finished(_source, event):
        output = clean(getattr(event, "output", "") or "")
        exit_hint = output.split("\n", 1)[0] if output.startswith("Exit code:") else ""
        _emit(
            queue,
            "tool_finished",
            role=_role_from_event(event),
            message=_tool_message(event, finished=True),
            filename=_tool_filename(getattr(event, "tool_args", None)),
            exit_hint=exit_hint,
        )

    @crewai_event_bus.on(ToolUsageErrorEvent)
    def on_tool_error(_source, event):
        _emit(
            queue,
            "tool_error",
            role=_role_from_event(event),
            message=_tool_message(event),
            error=clean(getattr(event, "error", "") or "Tool failed"),
        )

    @crewai_event_bus.on(MCPToolExecutionStartedEvent)
    def on_mcp_started(_source, event):
        _emit(
            queue,
            "mcp_started",
            role=_role_from_event(event),
            tool_name=clean(getattr(event, "tool_name", "") or "an MCP tool"),
        )


def _role_from_event(event: Any) -> str:
    role = clean(getattr(event, "agent_role", "") or "")
    if role:
        return role
    agent = getattr(event, "agent", None) or getattr(event, "from_agent", None)
    return clean(getattr(agent, "role", "") or "")


def _task_label(event: Any) -> str:
    name = clean(getattr(event, "task_name", "") or "")
    task = getattr(event, "task", None) or getattr(event, "from_task", None)
    if not name and task is not None:
        name = clean(getattr(task, "name", "") or "")
    if name in TASK_LABELS:
        return TASK_LABELS[name]
    if name:
        return name.replace("_", " ")
    return "their assigned work"


def _tool_filename(args: Any) -> str:
    if isinstance(args, dict):
        return clean(args.get("filename") or "")
    return ""


def _tool_message(event: Any, finished: bool = False) -> str:
    tool_name = clean(getattr(event, "tool_name", "") or "")
    filename = _tool_filename(getattr(event, "tool_args", None))
    file_bit = f" `{filename}`" if filename else ""
    lowered = tool_name.lower()
    if "write" in lowered:
        return f"{'wrote' if finished else 'writing'}{file_bit or ' a sandbox file'}"
    if "read" in lowered:
        return f"{'read' if finished else 'reading'}{file_bit or ' a sandbox file'}"
    if "list" in lowered:
        return "listed sandbox files" if finished else "listing sandbox files"
    if "run" in lowered:
        return f"{'finished running' if finished else 'running'}{file_bit or ' a Python file'}"
    if tool_name:
        verb = "used" if finished else "using"
        return f"{verb} `{tool_name}`{file_bit}"
    return "used a tool" if finished else "using a tool"


def _log(state: dict[str, Any], who: str, what_html: str, role: str = "") -> None:
    state["log"].append(
        {
            "time": datetime.now().strftime("%H:%M:%S"),
            "who": who or "Crew",
            "what": what_html,
            "tone": log_tone(role),
        }
    )


def _set_stage(state: dict[str, Any], role: str, status: str, action: str = "") -> None:
    key = stage_key(role)
    if not key:
        return
    if status == "active":
        for other_key, info in state["stages"].items():
            if other_key != key and info["status"] == "active":
                info["status"] = "done"
                info["action"] = ""
    state["stages"][key]["status"] = status
    if action:
        state["stages"][key]["action"] = action
    elif status != "active":
        state["stages"][key]["action"] = ""


def _list_sandbox_files() -> list[str]:
    if not SANDBOX_DIR.exists():
        return []
    names = []
    for path in sorted(SANDBOX_DIR.iterdir(), key=lambda p: p.name.lower()):
        if path.name in SANDBOX_SKIP or path.name.startswith("."):
            continue
        names.append(path.name)
    return names


def _read_sandbox_file(name: str) -> str:
    path = SANDBOX_DIR / name
    if path.is_file():
        return path.read_text()
    return ""


def _refresh_artifacts(state: dict[str, Any], *, keep_output: bool = False) -> None:
    state["files"] = _list_sandbox_files()
    design = _read_sandbox_file("design.md")
    if design:
        state["design"] = design
    if keep_output and state["output"]:
        return
    summary = _read_sandbox_file("test_summary.md")
    if summary:
        state["output"] = summary


def _who(event: dict[str, Any]) -> str:
    return clean(event.get("role") or "") or "Crew"


def _on_sandbox(state: dict[str, Any], _event: dict[str, Any]) -> None:
    state["phase"] = "running"
    state["headline"] = "Preparing a fresh sandbox for the team…"
    _log(state, "Crew", "Resetting the sandbox and installing Gradio.")


def _on_crew_started(state: dict[str, Any], event: dict[str, Any]) -> None:
    state["phase"] = "running"
    state["headline"] = "The engineering crew is on the floor."
    _log(state, "Crew", f"Started <strong>{escape(event.get('name') or 'Engineering Team')}</strong>.")


def _on_agent_started(state: dict[str, Any], event: dict[str, Any]) -> None:
    who, task = _who(event), event.get("task") or "their assigned work"
    _set_stage(state, event.get("role") or "", "active", f"Working on {task}")
    state["headline"] = f"{who} is working on {task}."
    _log(state, who, f"Started <strong>{escape(task)}</strong>.", event.get("role") or "")


def _on_task_started(state: dict[str, Any], event: dict[str, Any]) -> None:
    who, task = _who(event), event.get("task") or "their assigned work"
    _set_stage(state, event.get("role") or "", "active", f"Working on {task}")
    state["headline"] = f"{who} picked up {task}."


def _on_tool_started(state: dict[str, Any], event: dict[str, Any]) -> None:
    who, message = _who(event), event.get("message") or "using a tool"
    _set_stage(state, event.get("role") or "", "active", message)
    state["headline"] = f"{who} is {message}."
    _log(state, who, format_inline_code(message), event.get("role") or "")


def _on_tool_finished(state: dict[str, Any], event: dict[str, Any]) -> None:
    who, message = _who(event), event.get("message") or "finished a tool"
    extra = f" ({escape(event['exit_hint'])})" if event.get("exit_hint") else ""
    _set_stage(state, event.get("role") or "", "active", message)
    if event.get("exit_hint"):
        _log(state, who, format_inline_code(message) + extra, event.get("role") or "")
    _refresh_artifacts(state)


def _on_tool_error(state: dict[str, Any], event: dict[str, Any]) -> None:
    who = _who(event)
    _set_stage(state, event.get("role") or "", "error", event.get("message") or "Tool failed")
    _log(state, who, f"Tool error: {escape(event.get('error'))}", event.get("role") or "")


def _on_mcp_started(state: dict[str, Any], event: dict[str, Any]) -> None:
    who = _who(event)
    tool_name = event.get("tool_name") or "an MCP tool"
    action = f"consulting docs via {tool_name}"
    _set_stage(state, event.get("role") or "", "active", action)
    state["headline"] = f"{who} is {action}."
    _log(state, who, format_inline_code(action), event.get("role") or "")


def _on_agent_completed(state: dict[str, Any], event: dict[str, Any]) -> None:
    who, task = _who(event), event.get("task") or "their assigned work"
    _set_stage(state, event.get("role") or "", "done")
    _log(state, who, f"Finished <strong>{escape(task)}</strong>.", event.get("role") or "")
    _refresh_artifacts(state)


def _on_task_completed(state: dict[str, Any], event: dict[str, Any]) -> None:
    _set_stage(state, event.get("role") or "", "done")
    _refresh_artifacts(state)


def _on_failure(state: dict[str, Any], event: dict[str, Any]) -> None:
    who = _who(event)
    error = event.get("error") or "Something failed"
    state["phase"] = "error"
    _set_stage(state, event.get("role") or "", "error", error)
    state["headline"] = f"{who} hit an error."
    _log(state, who, f"Error: {escape(error)}", event.get("role") or "")


def _on_crew_completed(state: dict[str, Any], event: dict[str, Any]) -> None:
    tokens = event.get("tokens") or 0
    token_bit = f" Used {int(tokens):,} tokens." if tokens else ""
    state["phase"] = "done"
    state["headline"] = f"Build complete.{token_bit}"
    for info in state["stages"].values():
        if info["status"] == "active":
            info["status"] = "done"
    _log(state, "Crew", "All stations finished.")
    _refresh_artifacts(state)


def _on_done(state: dict[str, Any], event: dict[str, Any]) -> None:
    output = event.get("output") or ""
    if output:
        state["output"] = output
    if state["phase"] != "error":
        state["phase"] = "done"
        if not state["headline"].startswith("Build complete"):
            state["headline"] = "Build complete. Review the design, files, and final write-up."
    _refresh_artifacts(state, keep_output=bool(state["output"]))


def _on_error(state: dict[str, Any], event: dict[str, Any]) -> None:
    error = event.get("error") or "The crew stopped unexpectedly."
    state["phase"] = "error"
    state["headline"] = "The build stopped."
    _log(state, "Crew", f"Stopped: {escape(error)}")


_HANDLERS = {
    "sandbox": _on_sandbox,
    "crew_started": _on_crew_started,
    "agent_started": _on_agent_started,
    "task_started": _on_task_started,
    "tool_started": _on_tool_started,
    "tool_finished": _on_tool_finished,
    "tool_error": _on_tool_error,
    "mcp_started": _on_mcp_started,
    "agent_completed": _on_agent_completed,
    "task_completed": _on_task_completed,
    "agent_error": _on_failure,
    "task_failed": _on_failure,
    "crew_failed": _on_failure,
    "crew_completed": _on_crew_completed,
    "done": _on_done,
    "error": _on_error,
}
