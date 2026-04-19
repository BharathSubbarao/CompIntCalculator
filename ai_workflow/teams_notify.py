from __future__ import annotations

import os
import requests
from datetime import datetime


TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL", "").strip()


def send_teams_escalation(
    issue_number: int,
    step_name: str,
    error_text: str,
    workflow_id: str,
) -> None:
    """Send escalation alert to Microsoft Teams channel."""
    if not TEAMS_WEBHOOK_URL:
        print(f"[WARNING] TEAMS_WEBHOOK_URL not set. Escalation not sent.")
        return

    payload = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "summary": f"🚨 Workflow blocked for issue #{issue_number}",
        "themeColor": "FF0000",
        "sections": [
            {
                "activityTitle": f"❌ Workflow BLOCKED: Issue #{issue_number}",
                "activitySubtitle": f"Failed at: {step_name}",
                "facts": [
                    {"name": "Workflow ID", "value": workflow_id},
                    {"name": "Issue Number", "value": str(issue_number)},
                    {"name": "Step", "value": step_name},
                    {"name": "Time", "value": datetime.utcnow().isoformat() + "Z"},
                    {"name": "Status", "value": "🔴 REQUIRES HUMAN INTERVENTION"},
                ],
                "text": f"**Error Details:**\n```\n{error_text[:500]}\n```",
            }
        ],
        "potentialAction": [
            {
                "@type": "OpenUri",
                "name": "View Issue on GitHub",
                "targets": [
                    {
                        "os": "default",
                        "uri": f"https://github.com/BharathSubbarao/CompIntCalculator/issues/{issue_number}",
                    }
                ],
            }
        ],
    }

    try:
        response = requests.post(TEAMS_WEBHOOK_URL, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"[INFO] Teams escalation sent for issue #{issue_number}")
        else:
            print(f"[ERROR] Teams webhook returned {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Failed to send Teams notification: {e}")
