from __future__ import annotations

import json
import subprocess
from typing import Any

REPO_OWNER = "BharathSubbarao"
REPO_NAME = "CompIntCalculator"


def get_issue(issue_number: int) -> dict[str, Any]:
    try:
        result = subprocess.run(
            [
                "gh",
                "issue",
                "view",
                str(issue_number),
                "--repo",
                f"{REPO_OWNER}/{REPO_NAME}",
                "--json",
                "body,title,number",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=20,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as error:
        raise RuntimeError(f"Failed to fetch issue: {error.stderr}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Failed to parse issue data: {error}") from error


def update_issue_body(issue_number: int, body: str) -> None:
    try:
        subprocess.run(
            [
                "gh",
                "issue",
                "edit",
                str(issue_number),
                "--body",
                body,
                "--repo",
                f"{REPO_OWNER}/{REPO_NAME}",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=20,
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError(f"Failed to update issue: {error.stderr}") from error


def comment_issue(issue_number: int, body: str) -> None:
    try:
        subprocess.run(
            [
                "gh",
                "issue",
                "comment",
                str(issue_number),
                "--body",
                body,
                "--repo",
                f"{REPO_OWNER}/{REPO_NAME}",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=20,
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError(f"Failed to comment on issue: {error.stderr}") from error