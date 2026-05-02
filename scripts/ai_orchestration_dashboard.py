from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

STATE_DIR = Path(".workflow/state")

STATUS_ICON = {
    "PENDING": "⬜",
    "IN_PROGRESS": "🟡",
    "COMPLETED": "✅",
    "BLOCKED": "🔴",
    "FAILED": "❌",
}

STATUS_COLOR = {
    "PENDING": "#888888",
    "IN_PROGRESS": "#f0a500",
    "COMPLETED": "#28a745",
    "BLOCKED": "#dc3545",
    "FAILED": "#dc3545",
}


def parse_timestamp(value: str | None) -> datetime:
    """Parse ISO timestamps from workflow state; use minimum date when missing/invalid."""
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return datetime.min


def load_workflows() -> list[dict[str, Any]]:
    """Load all workflow state files, newest first by workflow updated_at."""
    if not STATE_DIR.exists():
        return []
    workflows: list[dict[str, Any]] = []
    for file_path in STATE_DIR.glob("*.json"):
        try:
            workflows.append(json.loads(file_path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    workflows.sort(key=lambda item: parse_timestamp(item.get("updated_at")), reverse=True)
    return workflows


def format_time(value: str | None) -> str:
    if not value:
        return "—"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone().strftime("%H:%M:%S")
    except ValueError:
        return value


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    if seconds < 60:
        return f"{seconds:.1f}s"
    return f"{int(seconds // 60)}m {int(seconds % 60)}s"


def render_step_card(step: dict[str, Any]) -> None:
    """Render a single step as a styled card."""
    status = step.get("status", "PENDING")
    icon = STATUS_ICON.get(status, "⬜")
    color = STATUS_COLOR.get(status, "#888")
    name = step.get("name", "")
    persona = step.get("persona", "")
    duration = format_duration(step.get("duration_seconds"))
    started = format_time(step.get("started_at"))
    ended = format_time(step.get("ended_at"))
    error = step.get("error")
    mode = step.get("execution_mode", "sequential")
    mode_badge = "🔀 parallel" if mode == "parallel" else "➡️ sequential"

    st.markdown(
        f"""
        <div style="
            border: 2px solid {color};
            border-radius: 10px;
            padding: 12px 16px;
            margin-bottom: 8px;
            background: {'#fff8e1' if status == 'IN_PROGRESS' else '#f8f9fa'};
        ">
            <div style="font-size:1.1em; font-weight:600;">{icon} {name}</div>
            <div style="color:#555; font-size:0.85em; margin-top:4px;">
                🤖 <code>{persona}</code> &nbsp;|&nbsp; {mode_badge}
            </div>
            <div style="margin-top:6px; font-size:0.85em; color:{color}; font-weight:600;">
                {status}
            </div>
            <div style="font-size:0.8em; color:#666; margin-top:4px;">
                ⏱ {duration} &nbsp;|&nbsp; Start: {started} &nbsp;|&nbsp; End: {ended}
            </div>
            {f'<div style="margin-top:6px; color:#dc3545; font-size:0.8em;">🚫 {error}</div>' if error else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_parallel_run_card(label: str, icon: str, run: dict[str, Any]) -> None:
    """Render a single parallel execution run card (unit_test_run or ui_test_run)."""
    status = run.get("status", "PENDING")
    color = STATUS_COLOR.get(status, "#888")
    status_icon = STATUS_ICON.get(status, "⬜")
    duration = format_duration(run.get("duration_seconds"))
    started = format_time(run.get("started_at"))
    ended = format_time(run.get("ended_at"))
    error = run.get("error")
    bg = "#fff8e1" if status == "IN_PROGRESS" else "#f8f9fa"

    st.markdown(
        f"""
        <div style="
            border: 2px solid {color};
            border-radius: 10px;
            padding: 10px 14px;
            background: {bg};
        ">
            <div style="font-size:1.0em; font-weight:600;">{status_icon} {icon} {label}</div>
            <div style="margin-top:5px; font-size:0.85em; color:{color}; font-weight:600;">
                {status}
            </div>
            <div style="font-size:0.8em; color:#666; margin-top:4px;">
                ⏱ {duration} &nbsp;|&nbsp; Start: {started} &nbsp;|&nbsp; End: {ended}
            </div>
            {f'<div style="margin-top:6px; color:#dc3545; font-size:0.8em;">🚫 {error}</div>' if error else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_parallel_execution_banner(parallel_execution: dict[str, Any] | None) -> None:
    """Render the parallel execution phase with live status cards for each test suite."""
    st.markdown(
        """
        <div style="
            border: 2px dashed #1a73e8;
            border-radius: 10px;
            padding: 8px 16px 4px 16px;
            margin-bottom: 6px;
            background: #e8f0fe;
            text-align: center;
        ">
            <div style="font-size:1.0em; font-weight:600; color:#1a73e8;">
                🔀 Parallel Execution Phase
            </div>
            <div style="font-size:0.78em; color:#555; margin-top:2px; margin-bottom:6px;">
                <code>bash scripts/run_parallel_testing.sh</code> — true OS-level parallelism
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    unit_run = (parallel_execution or {}).get("unit_test_run")
    ui_run = (parallel_execution or {}).get("ui_test_run")

    if unit_run is not None or ui_run is not None:
        col_unit, col_ui = st.columns(2)
        with col_unit:
            render_parallel_run_card("pytest", "🧪", unit_run or {})
        with col_ui:
            render_parallel_run_card("playwright", "🎭", ui_run or {})
    else:
        # Fallback for old state files without parallel_execution tracking
        st.markdown(
            "<div style='text-align:center; font-size:0.82em; color:#888; padding-bottom:6px;'>"
            "pytest &nbsp;‖&nbsp; playwright — status not tracked in this workflow run</div>",
            unsafe_allow_html=True,
        )


def render_pipeline(steps: list[dict[str, Any]], parallel_execution: dict[str, Any] | None) -> None:
    """Render the full pipeline: Steps 1–4 sequential (write phases), parallel execution banner, Step 5."""
    steps_by_id = {s["step_id"]: s for s in steps}
    arrow = "<div style='text-align:center; font-size:1.4em; color:#aaa;'>↓</div>"

    # Steps 1 and 2 — sequential
    for step_id in [1, 2]:
        if step := steps_by_id.get(step_id):
            render_step_card(step)
            st.markdown(arrow, unsafe_allow_html=True)

    # Step 3 — write-only (sequential)
    if step := steps_by_id.get(3):
        render_step_card(step)
        st.markdown(arrow, unsafe_allow_html=True)

    # Step 4 — write-only (sequential)
    if step := steps_by_id.get(4):
        render_step_card(step)
        st.markdown(arrow, unsafe_allow_html=True)

    # Parallel execution phase with live status cards
    render_parallel_execution_banner(parallel_execution)
    st.markdown(arrow, unsafe_allow_html=True)

    # Step 5 — sequential
    if step := steps_by_id.get(5):
        render_step_card(step)


def main() -> None:
    st.set_page_config(page_title="AI Orchestration Dashboard", layout="wide")

    st.title("🤖 AI Orchestration Dashboard")
    st.caption("Multi-agent pipeline — sequential write phases → parallel test execution")

    auto_refresh = st.sidebar.toggle("Auto-refresh", value=True)
    refresh_seconds = st.sidebar.slider(
        "Refresh interval (seconds)",
        min_value=2,
        max_value=60,
        value=5,
        disabled=not auto_refresh,
    )

    if auto_refresh:
        refresh_ms = refresh_seconds * 1000
        components.html(
            f"""
            <script>
            setTimeout(function() {{
              window.parent.location.reload();
            }}, {refresh_ms});
            </script>
            """,
            height=0,
        )
        st.caption(f"Auto-refreshing every {refresh_seconds}s.")

    workflows = load_workflows()
    if not workflows:
        st.info("No workflow state files found in .workflow/state/")
        st.stop()

    # Workflow selector
    st.sidebar.markdown("---")
    st.sidebar.subheader("Workflows")
    workflow_ids = [item.get("workflow_id", "unknown") for item in workflows]
    st.sidebar.caption("Most recently updated first.")
    selected_id = st.sidebar.selectbox("Select workflow", options=workflow_ids, index=0, label_visibility="collapsed")

    selected = next((w for w in workflows if w.get("workflow_id") == selected_id), workflows[0])
    steps = selected.get("steps", [])
    parallel_execution: dict[str, Any] = selected.get("parallel_execution", {})

    # Summary metrics — include parallel execution runs in active/blocked/completed counts
    overall_status = selected.get("status", "PENDING")
    par_runs = list(parallel_execution.values()) if parallel_execution else []
    active_agents = sum(1 for s in steps if s.get("status") == "IN_PROGRESS") + \
                    sum(1 for r in par_runs if r.get("status") == "IN_PROGRESS")
    blocked_count = sum(1 for s in steps if s.get("status") == "BLOCKED") + \
                    sum(1 for r in par_runs if r.get("status") == "BLOCKED")
    completed_count = sum(1 for s in steps if s.get("status") == "COMPLETED")
    total_duration = sum(s.get("duration_seconds") or 0 for s in steps) + \
                     sum(r.get("duration_seconds") or 0 for r in par_runs)

    st.markdown(f"### Issue #{selected.get('issue_number', '?')} — `{selected_id}`")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Status", f"{STATUS_ICON.get(overall_status, '')} {overall_status}")
    m2.metric("Active Agents", active_agents)
    m3.metric("Completed Steps", f"{completed_count} / {len(steps)}")
    m4.metric("Blocked", blocked_count)
    m5.metric("Total Duration", format_duration(total_duration if total_duration else None))

    st.markdown("---")

    # Pipeline view
    left, right = st.columns([2, 1])

    with left:
        st.subheader("Pipeline")
        render_pipeline(steps, parallel_execution)

    with right:
        st.subheader("Step Detail")
        step_options = {f"Step {s['step_id']}: {s['name']}": s for s in steps}
        selected_step_label = st.selectbox("Inspect step", options=list(step_options.keys()), label_visibility="visible")
        if selected_step_label:
            s = step_options[selected_step_label]
            st.json({
                "step_id": s.get("step_id"),
                "persona": s.get("persona"),
                "execution_mode": s.get("execution_mode"),
                "status": s.get("status"),
                "started_at": s.get("started_at"),
                "ended_at": s.get("ended_at"),
                "duration_seconds": s.get("duration_seconds"),
                "error": s.get("error"),
            })

        # Blocked errors panel — steps and parallel execution runs
        blocked_steps = [s for s in steps if s.get("status") == "BLOCKED"]
        blocked_runs = [
            (key, r) for key, r in parallel_execution.items() if r.get("status") == "BLOCKED"
        ] if parallel_execution else []
        if blocked_steps or blocked_runs:
            st.markdown("---")
            st.error(f"⛔ Workflow BLOCKED — {len(blocked_steps) + len(blocked_runs)} gate failure(s)")
            for s in blocked_steps:
                st.markdown(f"**Step {s['step_id']}: {s['name']}**")
                st.code(str(s.get("error", "Unknown error")), language="text")
            for key, r in blocked_runs:
                label = "pytest (Unit Tests)" if key == "unit_test_run" else "playwright (UI Regression)"
                st.markdown(f"**Parallel Execution — {label}**")
                st.code(str(r.get("error", "Unknown error")), language="text")

    st.markdown("---")
    st.caption(
        f"Updated: {format_time(selected.get('updated_at'))}  |  "
        "Pipeline: Step 1 → Step 2 → Step 3 (write) → Step 4 (write) → [pytest ‖ playwright] → Step 5"
    )


if __name__ == "__main__":
    main()
