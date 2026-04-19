from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

STATE_DIR = Path(".workflow/state")


def load_all_workflows() -> list[dict]:
    """Load all workflow state files."""
    if not STATE_DIR.exists():
        return []
    
    data = []
    for p in sorted(STATE_DIR.glob("*.json"), reverse=True):
        try:
            data.append(json.loads(p.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, IOError):
            pass
    
    return data


def format_timestamp(ts: str | None) -> str:
    """Format ISO timestamp for display."""
    if not ts:
        return "—"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError):
        return str(ts)


def main() -> None:
    st.set_page_config(
        page_title="AI Workflow Dashboard",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.title("🤖 AI Issue Workflow Dashboard")
    st.caption("Real-time monitoring of CompIntCalculator issue workflows")

    # Load workflows
    workflows = load_all_workflows()

    if not workflows:
        st.info(
            "📭 No workflows found yet.\n\n"
            "Start a workflow in Copilot Chat by saying: **'Start work on git issue #1'**"
        )
        st.stop()

    # Workflow selector
    latest = workflows[0]
    all_workflow_ids = [w["workflow_id"] for w in workflows]

    selected_workflow_id = st.selectbox(
        "Select Workflow:",
        options=all_workflow_ids,
        index=0,
    )

    # Find selected workflow
    selected_workflow = next(
        (w for w in workflows if w["workflow_id"] == selected_workflow_id),
        latest,
    )

    # Display main metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Issue #", selected_workflow["issue_number"])
    with col2:
        st.metric("Status", selected_workflow["status"])
    with col3:
        st.metric("Current Step", selected_workflow["current_step"])
    with col4:
        st.metric("Created At", format_timestamp(selected_workflow["created_at"]))

    st.divider()

    # Steps table
    st.subheader("📊 Step Progress")

    rows = []
    total_duration = 0.0

    for step in selected_workflow["steps"]:
        rows.append(
            {
                "Step": step["step_id"],
                "Name": step["name"],
                "Status": step["status"],
                "Started": format_timestamp(step["started_at"]),
                "Ended": format_timestamp(step["ended_at"]),
                "Duration (s)": (
                    f"{step['duration_seconds']:.1f}"
                    if step.get("duration_seconds")
                    else "—"
                ),
            }
        )
        if step.get("duration_seconds"):
            total_duration += step["duration_seconds"]

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Show error if blocked
    if selected_workflow["status"] == "BLOCKED":
        st.divider()
        st.error(
            "⚠️ **Workflow Blocked**\n\n"
            "An escalation has been sent to Microsoft Teams. "
            "Please check Teams for details and take corrective action."
        )

        # Find blocked step
        blocked_step = next(
            (s for s in selected_workflow["steps"] if s["status"] == "BLOCKED"),
            None,
        )
        if blocked_step:
            st.code(blocked_step.get("error", "Unknown error"), language="plaintext")

    # Summary stats
    st.divider()
    st.subheader("⏱️ Timing Summary")

    c1, c2, c3 = st.columns(3)
    with c1:
        created = datetime.fromisoformat(
            selected_workflow["created_at"].replace("Z", "+00:00")
        )
        updated = datetime.fromisoformat(
            selected_workflow["updated_at"].replace("Z", "+00:00")
        )
        elapsed = (updated - created).total_seconds()
        st.metric("Total Elapsed (s)", f"{elapsed:.1f}")
    with c2:
        st.metric("Total Step Duration (s)", f"{total_duration:.1f}")
    with c3:
        completed_steps = len([s for s in selected_workflow["steps"] if s["status"] == "COMPLETED"])
        st.metric("Completed Steps", f"{completed_steps} / 5")

    # Auto-refresh hint
    st.divider()
    st.caption(
        "💡 **Tip:** Press 'R' or refresh the page to see latest status. "
        "Workflows auto-update every few seconds."
    )


if __name__ == "__main__":
    main()
