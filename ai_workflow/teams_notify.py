from __future__ import annotations

import os
from datetime import datetime

import requests

TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL", "").strip()


def send_teams_escalation(issue_number: int, step_name: str, error_text: str, workflow_id: str) -> None:
    if not TEAMS_WEBHOOK_URL:
        print("[WARNING] TEAMS_WEBHOOK_URL not set. Escalation not sent.")
        return

    payload = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": f"Workflow blocked for issue #{issue_number}",
        "themeColor": "FF0000",
        "sections": [
            {
                "activityTitle": f"Workflow BLOCKED: Issue #{issue_number}",
                "activitySubtitle": f"Failed at: {step_name}",
                "facts": [
                    {"name": "Workflow ID", "value": workflow_id},
                    {"name": "Issue Number", "value": str(issue_number)},
                    {"name": "Step", "value": step_name},
                    {"name": "Time", "value": datetime.utcnow().isoformat() + "Z"},
                ],
                "text": f"Error details:\n```\n{error_text[:500]}\n```",
            }
        ],
    }

    try:
        requests.post(TEAMS_WEBHOOK_URL, json=payload, timeout=10)
    except Exception as error:
        print(f"[ERROR] Failed to send Teams notification: {error}")