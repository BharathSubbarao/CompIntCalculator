from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

STATE_DIR = Path(".workflow/state")


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
        return "-"

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone().strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return value


def main() -> None:
    st.set_page_config(page_title="AI Workflow Dashboard", layout="wide")

    st.title("AI Workflow Dashboard")
    st.caption("Live status for issue workflows")

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
        st.caption(f"Auto-refreshing every {refresh_seconds} seconds.")

    workflows = load_workflows()
    if not workflows:
        st.info("No workflow state files found in .workflow/state")
        st.stop()

    workflow_ids = [item.get("workflow_id", "unknown") for item in workflows]
    st.caption("Showing the most recently updated workflow first.")
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

    st.caption("Use sidebar controls to adjust auto-refresh behavior.")


if __name__ == "__main__":
    main()
