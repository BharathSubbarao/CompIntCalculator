from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

STATE_DIR = Path(".workflow/state")


def load_workflows() -> list[dict[str, Any]]:
    """Load all workflow state files, newest first by file name."""
    if not STATE_DIR.exists():
        return []

    workflows: list[dict[str, Any]] = []
    for file_path in sorted(STATE_DIR.glob("*.json"), reverse=True):
        try:
            workflows.append(json.loads(file_path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue

    return workflows


def format_time(value: str | None) -> str:
    if not value:
        return "-"

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return value


def main() -> None:
    st.set_page_config(page_title="AI Workflow Dashboard", layout="wide")

    st.title("AI Workflow Dashboard")
    st.caption("Live status for issue workflows")

    workflows = load_workflows()
    if not workflows:
        st.info("No workflow state files found in .workflow/state")
        st.stop()

    workflow_ids = [item.get("workflow_id", "unknown") for item in workflows]
    selected_id = st.selectbox("Workflow", options=workflow_ids, index=0)

    selected = next(
        (item for item in workflows if item.get("workflow_id") == selected_id),
        workflows[0],
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Issue", f"#{selected.get('issue_number', '-')}")
    col2.metric("Status", str(selected.get("status", "-")))
    col3.metric("Current Step", str(selected.get("current_step", "-")))
    col4.metric("Updated", format_time(selected.get("updated_at")))

    step_rows: list[dict[str, Any]] = []
    for step in selected.get("steps", []):
        step_rows.append(
            {
                "Step": step.get("step_id"),
                "Name": step.get("name"),
                "Status": step.get("status"),
                "Start": format_time(step.get("started_at")),
                "End": format_time(step.get("ended_at")),
                "Duration (s)": step.get("duration_seconds"),
            }
        )

    st.subheader("Step Timeline")
    st.dataframe(step_rows, use_container_width=True, hide_index=True)

    blocked = next(
        (step for step in selected.get("steps", []) if step.get("status") == "BLOCKED"),
        None,
    )
    if blocked:
        st.error("Workflow is blocked and requires human intervention.")
        st.code(str(blocked.get("error", "Unknown error")), language="text")

    st.caption("Refresh the page to see newer workflow updates.")


if __name__ == "__main__":
    main()
