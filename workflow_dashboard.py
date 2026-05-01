from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

STATE_DIR = Path(".workflow/state")

# Steps that run in parallel — rendered side-by-side in the pipeline view.
PARALLEL_STEPS = {3, 4}

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


def render_pipeline(steps: list[dict[str, Any]]) -> None:
    """Render the full pipeline with parallel step 3+4 side-by-side."""
    sequential_before = [s for s in steps if s["step_id"] < 3]
    parallel = [s for s in steps if s["step_id"] in PARALLEL_STEPS]
    sequential_after = [s for s in steps if s["step_id"] > 4]

    # Steps 1 and 2
    for step in sequential_before:
        render_step_card(step)
        st.markdown("<div style='text-align:center; font-size:1.4em; color:#aaa;'>↓</div>", unsafe_allow_html=True)

    # Steps 3 + 4 side by side
    if parallel:
        st.markdown(
            "<div style='text-align:center; font-size:0.8em; color:#888; margin-bottom:4px;'>"
            "— parallel execution —</div>",
            unsafe_allow_html=True,
        )
        cols = st.columns(len(parallel))
        for col, step in zip(cols, parallel):
            with col:
                render_step_card(step)
        st.markdown("<div style='text-align:center; font-size:1.4em; color:#aaa;'>↓</div>", unsafe_allow_html=True)

    # Step 5
    for step in sequential_after:
        render_step_card(step)


def main() -> None:
    st.set_page_config(page_title="AI Workflow Dashboard", layout="wide")

    st.title("🤖 AI Workflow Dashboard")
    st.caption("Multi-agent orchestration — live pipeline view")

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

    # Summary metrics
    overall_status = selected.get("status", "PENDING")
    active_agents = sum(1 for s in steps if s.get("status") == "IN_PROGRESS")
    blocked_count = sum(1 for s in steps if s.get("status") == "BLOCKED")
    completed_count = sum(1 for s in steps if s.get("status") == "COMPLETED")
    total_duration = sum(s.get("duration_seconds") or 0 for s in steps)

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
        render_pipeline(steps)

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

        # Blocked errors panel
        blocked_steps = [s for s in steps if s.get("status") == "BLOCKED"]
        if blocked_steps:
            st.markdown("---")
            st.error(f"⛔ Workflow BLOCKED — {len(blocked_steps)} gate failure(s)")
            for s in blocked_steps:
                st.markdown(f"**Step {s['step_id']}: {s['name']}**")
                st.code(str(s.get("error", "Unknown error")), language="text")

        # Parallel step logs
        log_dir = Path(".workflow/logs")
        parallel_logs = {
            3: log_dir / f"{selected_id}-unit-tester.log",
            4: log_dir / f"{selected_id}-ui-tester.log",
        }
        log_labels = {3: "Unit Tester log", 4: "UI Tester log"}
        any_log = any(p.exists() for p in parallel_logs.values())
        if any_log:
            st.markdown("---")
            st.subheader("Parallel Step Logs")
            for step_id, log_path in parallel_logs.items():
                if log_path.exists():
                    with st.expander(f"📄 Step {step_id}: {log_labels[step_id]}"):
                        st.code(log_path.read_text(encoding="utf-8")[-3000:], language="text")

    st.markdown("---")
    st.caption(
        f"Updated: {format_time(selected.get('updated_at'))}  |  "
        "Pipeline: Step 1 → Step 2 → (Step 3 ‖ Step 4) → Step 5"
    )


if __name__ == "__main__":
    main()
