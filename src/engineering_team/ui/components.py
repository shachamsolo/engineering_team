"""HTML fragments and renderers for the live build floor."""

from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Any

DESIGN_PLACEHOLDER = "_Design will appear here once the Engineering Lead finishes._"
OUTPUT_PLACEHOLDER = "_The crew's final write-up will land here._"
IDLE_HEADLINE = "Ready when you are. Paste a product brief and start the build."
EMPTY_LOG = "The floor is quiet. Start a build to watch the team work."
EMPTY_FILES = "No application files in the sandbox yet."

HERO_HTML = """
<div class="hero">
  <div class="kicker">Live build floor</div>
  <h1>Engineering Team</h1>
  <p>Four specialists take a product brief from design through backend, Gradio UI, and tests. Watch each station as the app is being built.</p>
</div>
"""

SANDBOX_SKIP = {
    ".venv",
    ".python-version",
    ".gitignore",
    "pyproject.toml",
    "uv.lock",
    "__pycache__",
    ".git",
}

TASK_LABELS = {
    "design_task": "system design",
    "code_task": "backend implementation",
    "frontend_task": "Gradio UI",
    "test_task": "unit tests",
}

STAGE_FLAG = {
    "waiting": "WAIT",
    "active": "LIVE",
    "done": "DONE",
    "error": "ERR",
}

STATUS_DOT = {
    "running": "live",
    "done": "done",
    "error": "error",
}

LOG_TONE = {
    "engineering_lead": "lead",
    "backend_engineer": "backend",
    "frontend_engineer": "frontend",
    "test_engineer": "test",
}


@dataclass(frozen=True)
class Stage:
    key: str
    role: str
    station: str
    title: str
    idle: str
    active: str
    done: str


STAGES = [
    Stage(
        key="engineering_lead",
        role="Engineering Lead",
        station="01",
        title="Design",
        idle="Waiting to take the brief",
        active="Turning requirements into a build plan",
        done="Design handed to the engineers",
    ),
    Stage(
        key="backend_engineer",
        role="Backend Engineer",
        station="02",
        title="Backend",
        idle="Waiting on the design",
        active="Writing and checking Python modules",
        done="Backend modules are in the sandbox",
    ),
    Stage(
        key="frontend_engineer",
        role="Frontend Engineer",
        station="03",
        title="Frontend",
        idle="Waiting on the backend",
        active="Building the Gradio interface",
        done="App UI is in the sandbox",
    ),
    Stage(
        key="test_engineer",
        role="Test Engineer",
        station="04",
        title="Tests",
        idle="Waiting on implementation",
        active="Writing and running unit tests",
        done="Tests written and executed",
    ),
]

STAGE_BY_ROLE = {stage.role.lower(): stage.key for stage in STAGES}


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def escape(value: Any) -> str:
    return html.escape(clean(value), quote=True)


def format_inline_code(message: str) -> str:
    escaped = escape(message)
    parts = escaped.split("`")
    if len(parts) < 3:
        return escaped
    rendered = []
    for index, part in enumerate(parts):
        if index % 2 == 1 and index < len(parts) - 1:
            rendered.append(f"<code>{part}</code>")
        else:
            rendered.append(part)
    return "".join(rendered)


def stage_key(role: str) -> str | None:
    normalized = role.lower().strip()
    if not normalized:
        return None
    if normalized in STAGE_BY_ROLE:
        return STAGE_BY_ROLE[normalized]
    for stage in STAGES:
        if stage.role.lower() in normalized or normalized in stage.role.lower():
            return stage.key
    return None


def log_tone(role: str) -> str:
    return LOG_TONE.get(stage_key(role) or "", "crew")


def default_stage_action(stage: Stage, status: str) -> str:
    return {
        "waiting": stage.idle,
        "active": stage.active,
        "done": stage.done,
        "error": "Stopped with an error",
    }[status]


def render_status(state: dict[str, Any]) -> str:
    copy = escape(state["headline"])
    dot = STATUS_DOT.get(state["phase"], "")
    return (
        '<div class="status-strip">'
        f'<span class="status-dot {dot}"></span>'
        f'<div class="status-copy">{copy}</div>'
        "</div>"
    )


def render_pipeline(state: dict[str, Any]) -> str:
    cards = []
    for stage in STAGES:
        info = state["stages"][stage.key]
        status = info["status"]
        action = info["action"] or default_stage_action(stage, status)
        css = status if status != "waiting" else ""
        cards.append(
            f'<article class="stage {css}">'
            f'<div class="stage-station">STATION {stage.station}</div>'
            f'<div class="stage-role">{escape(stage.role)}</div>'
            f'<div class="stage-title">{escape(stage.title)}</div>'
            f'<div class="stage-action">{escape(action)}</div>'
            f'<div class="stage-flag">{STAGE_FLAG[status]}</div>'
            "</article>"
        )
    return f'<div class="pipeline">{"".join(cards)}</div>'


def render_log(state: dict[str, Any]) -> str:
    if not state["log"]:
        return f'<div class="log-panel"><div class="empty-note">{EMPTY_LOG}</div></div>'
    items = [
        (
            '<div class="log-item">'
            f'<div class="log-time">{escape(entry["time"])}</div>'
            f'<div class="log-agent {escape(entry["tone"])}">{escape(entry["who"])}</div>'
            f'<div class="log-msg">{entry["what"]}</div>'
            "</div>"
        )
        for entry in state["log"]
    ]
    return f'<div class="log-panel">{"".join(items)}</div>'


def render_files(names: list[str]) -> str:
    if not names:
        return f'<div class="empty-note">{EMPTY_FILES}</div>'
    chips = "".join(f'<span class="file-chip">{escape(name)}</span>' for name in names)
    return f'<div class="file-grid">{chips}</div>'
