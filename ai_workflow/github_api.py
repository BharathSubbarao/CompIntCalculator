from __future__ import annotations

import subprocess
import json
from typing import Any


REPO_OWNER = "BharathSubbarao"
REPO_NAME = "CompIntCalculator"


def get_issue(issue_number: int) -> dict[str, Any]:
    """Fetch issue from GitHub using gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "issue", "view", str(issue_number), "--repo", f"{REPO_OWNER}/{REPO_NAME}", "--json", "body,title,number"],
            capture_output=True,
            text=True,
            check=True,
            timeout=20,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to fetch issue: {e.stderr}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse issue data: {e}")


def update_issue_body(issue_number: int, body: str) -> None:
    """Update issue body on GitHub using gh CLI."""
    try:
        subprocess.run(
            ["gh", "issue", "edit", str(issue_number), "--body", body, "--repo", f"{REPO_OWNER}/{REPO_NAME}"],
            capture_output=True,
            text=True,
            check=True,
            timeout=20,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to update issue: {e.stderr}")


def comment_issue(issue_number: int, body: str) -> None:
    """Post a comment on an issue using gh CLI."""
    try:
        subprocess.run(
            ["gh", "issue", "comment", str(issue_number), "--body", body, "--repo", f"{REPO_OWNER}/{REPO_NAME}"],
            capture_output=True,
            text=True,
            check=True,
            timeout=20,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to comment on issue: {e.stderr}")
