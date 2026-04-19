# AI Workflow Orchestrator Setup Guide

This document explains how to set up and run the automated issue workflow system for CompIntCalculator.

## 📋 Overview

The AI workflow system consists of:
1. **Copilot Agent** (.github/agents/issue-workflow.agent.md): Orchestrates work on GitHub issues
2. **FastAPI Orchestrator Service** (ai_workflow/): Manages workflow state and execution
3. **Workflow Dashboard** (workflow_dashboard.py): Displays real-time progress for stakeholders
4. **Microsoft Teams Escalation**: Sends alerts when workflows are blocked

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Set Up GitHub Authentication (Required)

The orchestrator uses GitHub CLI (`gh`) with your authenticated session. You must authenticate first.

**Authenticate with GitHub CLI:**

```bash
# Authenticate with GitHub
gh auth login

# Verify authentication
gh auth status
```

Expected output:
```
github.com
  ✓ Logged in to github.com account YourUsername (keyring)
  - Active account: true
  - Git operations protocol: https
  - Token: gho_****...
  - Token scopes: 'gist', 'read:org', 'repo', 'workflow'
```

The token is stored securely in your system keyring and is automatically used by the orchestrator.

### Step 3: Set Up Microsoft Teams Webhook (for escalations)

1. Open your Teams channel where you want alerts (e.g., `#dev-alerts`)
2. Click **⋯ More options** → **Connectors**
3. Search for **"Incoming Webhook"** and click **Add**
4. Name it: `AI Workflow Escalations`
5. Click **Create**
6. Copy the webhook URL

Add to your environment:

```bash
export TEAMS_WEBHOOK_URL="https://outlook.webhook.office.com/webhookb2/..."
```

Or create a `.env` file in the project root:

```env
GITHUB_TOKEN=your_token_here
TEAMS_WEBHOOK_URL=https://outlook.webhook.office.com/webhookb2/...
```

### Step 4: Start the Orchestrator Service

```bash
cd /Users/bsubbarao/MYDATA/CompIntCalculator

# Terminal 1: Start the orchestrator
uvicorn ai_workflow.main:app --reload --port 8090
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8090
```

### Step 5: Start the Dashboard (Optional)

In a separate terminal:

```bash
# Terminal 2: Start the dashboard
streamlit run workflow_dashboard.py --server.port 8510
```

Dashboard opens at: http://localhost:8510

### Step 6: Trigger a Workflow from Copilot Chat

In VS Code, open Copilot Chat and say:

```
Start work on git issue #1
```

Watch the orchestrator terminal for real-time progress, and the dashboard for step details.

## 📊 Dashboard Features

The real-time dashboard shows:
- Overall workflow status
- Current step and progress
- Start/end timestamps for each step
- Duration of each step (in seconds)
- Error details if workflow is blocked
- Timing summary (elapsed, completed steps)

Access at: **http://localhost:8510**

## 🔄 Workflow Steps (In Order)

1. **Product Owner Issue Refinement** (step 1)
   - Standardizes issue format to required template
   - Extracts problem statement, acceptance criteria, UI expectations, edge cases, tests

2. **Developer Implementation** (step 2)
   - Creates feature branch
   - Implements code changes per acceptance criteria
   - Commits changes

3. **Unit Testing** (step 3)
   - Runs existing tests: `bash ./scripts/run_tests_with_log.sh`
   - Adds/modifies unit tests as needed
   - Fails if any test doesn't pass

4. **UI Regression Testing** (step 4)
   - Runs Playwright tests: `bash ./scripts/run_ui_regression.sh`
   - Adds/modifies UI tests as needed
   - Comments results on GitHub issue
   - Fails if any test doesn't pass

5. **Pull Request Creation** (step 5)
   - Creates PR with `gh pr create`
   - PR ready for human review

## 🚨 Escalation & Blocking

If **any step fails**:
1. Workflow status changes to **BLOCKED**
2. Error details posted to Microsoft Teams channel
3. Dashboard shows error message and error details
4. Workflow halts (does not proceed to next step)
5. Human intervention required to fix the issue

On the dashboard, blocked workflows show:
- 🔴 Red status indicator
- Error message in code block
- Instructions to check Teams

## 📁 File Structure

```
CompIntCalculator/
├── .github/
│   ├── agents/
│   │   └── issue-workflow.agent.md          # Main agent definition
│   ├── instructions/
│   │   └── workflow-trigger.instructions.md # Trigger instructions
│   └── prompts/
│       └── start-issue-workflow.prompt.md   # Prompt template
│
├── ai_workflow/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── models.py               # Pydantic data models
│   ├── state_store.py          # Workflow state persistence
│   ├── teams_notify.py         # Teams webhook integration
│   ├── github_api.py           # GitHub API calls
│   ├── personas.py             # Workflow step implementations
│   └── workflow.py             # Workflow orchestration logic
│
├── .workflow/
│   └── state/                  # Workflow state files (auto-created)
│
├── workflow_dashboard.py       # Streamlit dashboard
├── requirements.txt            # Updated with new dependencies
└── ...
```

## 🔍 Monitoring & Debugging

### View Orchestrator Logs

Terminal 1 (orchestrator) shows:
```
[WORKFLOW issue-1-20260419141530-abc12345] Starting for issue #1
[STEP 1] Started: Product Owner Issue Refinement
[STEP 1] Completed in 5.2s: Product Owner Issue Refinement
[STEP 2] Started: Developer Implementation
...
```

### View Workflow State File

```bash
cat .workflow/state/issue-1-*.json | jq .
```

Shows current status, all steps, timestamps, and errors.

### Check Health of Orchestrator

```bash
curl http://localhost:8090/health
# Output: {"status":"ok","service":"Issue Workflow Orchestrator"}
```

### Get Workflow Status from API

```bash
curl http://localhost:8090/workflows/issue-1-20260419141530-abc12345 | jq .
```

## 🐛 Troubleshooting

### "Orchestrator service not running"
**Problem**: Chat says orchestrator is unreachable
**Solution**: Start it with: `uvicorn ai_workflow.main:app --reload --port 8090`

### "GitHub authentication failed" (Step 1 fails)
**Problem**: Workflow fails at step 1 with 401 Unauthorized error
**Solution**: Verify GitHub CLI authentication:
```bash
gh auth status
```
If not authenticated, run: `gh auth login`

### "TEAMS_WEBHOOK_URL not set"
**Problem**: Escalations don't appear in Teams
**Solution**: Set webhook URL: `export TEAMS_WEBHOOK_URL="https://outlook.webhook.office.com/..."` or add to .env
Note: Escalations are optional; if not set, workflow still works but Teams won't get alerts.

### "gh: command not found"
**Problem**: Step 5 (PR creation) fails
**Solution**: Install GitHub CLI: `brew install gh` (macOS) or follow https://cli.github.com/

### Tests fail in step 3 or 4
**Problem**: Workflow blocked at testing
**Solution**:
1. Check error in dashboard or orchestrator logs
2. Fix the code issue
3. Restart workflow (create new issue or manually retry)

## 📝 Workflow State Files

Workflow state is saved to `.workflow/state/issue-{number}-{timestamp}-{uuid}.json`

Example structure:
```json
{
  "workflow_id": "issue-1-20260419141530-abc12345",
  "issue_number": 1,
  "status": "IN_PROGRESS",
  "current_step": 2,
  "created_at": "2026-04-19T14:15:30Z",
  "updated_at": "2026-04-19T14:18:45Z",
  "steps": [
    {
      "step_id": 1,
      "name": "Product Owner Issue Refinement",
      "persona": "product_owner",
      "status": "COMPLETED",
      "started_at": "2026-04-19T14:15:30Z",
      "ended_at": "2026-04-19T14:15:35Z",
      "duration_seconds": 5.2,
      "output": { "issue_updated": true, "template_applied": true },
      "error": null
    },
    ...
  ]
}
```

## 🔐 Security Notes

- **GitHub Token**: Has `repo` and `issues` scope. Keep it secret.
- **Teams Webhook**: Only receives workflow notifications. Regenerate if compromised.
- **State Files**: Stored locally in `.workflow/state/`. Consider git-ignoring for CI/CD environments.

## 📞 Support

- **Workflow hangs?** Check if orchestrator is still running in Terminal 1
- **Dashboard not updating?** Refresh page or check orchestrator logs
- **Teams not receiving alerts?** Verify TEAMS_WEBHOOK_URL is set correctly
- **PR not created?** Verify GitHub auth: `gh auth status`

---

**Next Steps:**
1. Configure GitHub token and Teams webhook
2. Start orchestrator: `uvicorn ai_workflow.main:app --reload --port 8090`
3. (Optional) Start dashboard: `streamlit run workflow_dashboard.py`
4. Test in Copilot Chat: Say "Start work on git issue #1"
