# 🤖 AI Issue Workflow System

Automated multi-persona workflow for CompIntCalculator GitHub issues using GitHub Copilot in VS Code.

## Overview

This system automates the entire lifecycle of a GitHub issue:

```
User says in Copilot Chat:
"Start work on git issue #1"
              ↓
Copilot Agent Triggered
              ↓
FastAPI Orchestrator processes 5 steps:
  1️⃣  Product Owner → Refine issue template
  2️⃣  Developer    → Create branch & implement
  3️⃣  Unit Tester  → Run & fix unit tests
  4️⃣  UI Tester    → Run & fix UI tests
  5️⃣  Reviewer     → Create PR for human review
              ↓
On Success: PR is ready for review ✅
On Failure: Teams alert sent 🚨 → Workflow blocked → Awaits human fix
```

## ✨ Key Features

✅ **Multi-Persona Workflow** — 5 autonomous agents in strict sequence
✅ **Live Dashboard** — Real-time progress tracking for stakeholders (step status, timestamps, durations)  
✅ **Teams Integration** — Instant escalation alerts when workflows block
✅ **State Persistence** — Workflow progress saved to JSON (auditable, version-controllable)
✅ **Auto-Recovery** — Tests fixed automatically; manual intervention required for other failures
✅ **GitHub Integration** — Updates issues, comments results, creates PRs via GitHub API

## 🚀 Quick Start (2 minutes)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Configuration

Copy and customize environment file:

```bash
cp .env.example .env
```

Edit `.env` to add:
- **GITHUB_TOKEN**: Personal access token from GitHub (https://github.com/settings/tokens)
- **TEAMS_WEBHOOK_URL**: Incoming webhook from Teams channel

### 3. Run Validation

```bash
bash scripts/validate-workflow-setup.sh
```

### 4. Start Orchestrator

Terminal 1:
```bash
uvicorn ai_workflow.main:app --reload --port 8090
```

### 5. (Optional) Start Dashboard

Terminal 2:
```bash
streamlit run workflow_dashboard.py
```

Open dashboard: **http://localhost:8510**

### 6. Trigger Workflow

In VS Code Copilot Chat, say:

```
Start work on git issue #1
```

Watch the orchestrator terminal and dashboard for progress.

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| [AI_WORKFLOW_SETUP.md](AI_WORKFLOW_SETUP.md) | Detailed setup guide, troubleshooting |
| [.github/agents/issue-workflow.agent.md](.github/agents/issue-workflow.agent.md) | Agent logic (step details, standards) |
| [.github/instructions/workflow-trigger.instructions.md](.github/instructions/workflow-trigger.instructions.md) | Copilot trigger conditions |

## 📊 Dashboard Features

Real-time monitoring of workflow progress:

- **Overall Status**: PENDING → IN_PROGRESS → COMPLETED or BLOCKED
- **Current Step**: Which of the 5 steps is running
- **Timestamps**: Start/end times for each step
- **Durations**: How long each step took (in seconds)
- **Error Details**: If blocked, shows the error message
- **Timing Summary**: Total elapsed time, completed steps

Access at: http://localhost:8510

## 🔄 Workflow Steps

### Step 1: Product Owner Issue Refinement (2-5 sec)
Standardizes issue format:
- Extracts problem statement from original issue
- Applies required template (criteria, UI expectations, edge cases, tests)
- Updates issue body on GitHub

### Step 2: Developer Implementation (variable, typically 1-5 min)
Creates feature and codes solution:
- Creates feature branch: `feature/issue-{number}`
- Implements changes per acceptance criteria
- Commits with message: `[Issue #{number}] description`

### Step 3: Unit Testing (5-30 sec)
Ensures code quality:
- Runs: `bash ./scripts/run_tests_with_log.sh`
- Adds/modifies unit tests as needed
- **Blocks if any test fails** ❌

### Step 4: UI Regression Testing (20-120 sec)
Ensures no UI breakage:
- Runs: `bash ./scripts/run_ui_regression.sh`
- Adds/modifies Playwright tests as needed
- Comments results on GitHub issue
- **Blocks if any test fails** ❌

### Step 5: Pull Request Creation (2-5 sec)
Opens PR for human review:
- Uses `gh pr create` to open PR
- PR title: `Issue #N: Automated implementation`
- Only runs if all prior steps succeed ✅

## 🚨 Escalation & Blocking

When a step fails:

1. **Workflow Status** → BLOCKED
2. **Teams Alert** → Sent immediately with error details
3. **Dashboard** → Shows error message and error details
4. **Workflow Halts** → Does not proceed to next step
5. **Human Action Required** → Fix the issue, restart workflow

Example Teams alert:
```
❌ Workflow BLOCKED: Issue #1
Failed at: Unit Testing
Error: 2 unit tests failing in test_app.py
Status: 🔴 REQUIRES HUMAN INTERVENTION
```

## 📁 Project Structure

```
CompIntCalculator/
├── .github/
│   ├── agents/
│   │   └── issue-workflow.agent.md          ← Main agent logic
│   ├── instructions/
│   │   └── workflow-trigger.instructions.md ← Trigger setup
│   └── prompts/
│       └── start-issue-workflow.prompt.md   ← Prompt template
│
├── ai_workflow/                  ← Orchestrator service
│   ├── __init__.py
│   ├── main.py                   ← FastAPI entry point
│   ├── models.py                 ← Pydantic schemas
│   ├── state_store.py            ← Persistence layer
│   ├── teams_notify.py           ← Teams escalation
│   ├── github_api.py             ← GitHub API wrapper
│   ├── personas.py               ← Step implementations
│   └── workflow.py               ← Orchestration logic
│
├── .workflow/
│   └── state/                    ← Workflow state files (JSON)
│
├── workflow_dashboard.py         ← Streamlit dashboard
├── AI_WORKFLOW_SETUP.md          ← Setup guide
├── .env.example                  ← Config template
├── requirements.txt              ← Python dependencies
└── scripts/
    ├── validate-workflow-setup.sh ← Validation script
    ├── run_tests_with_log.sh     ← Unit test runner
    └── run_ui_regression.sh      ← UI test runner
```

## 🔌 Integration Points

### GitHub API
- Fetch issue details
- Update issue body with template
- Post comments with results
- Create pull requests

### GitHub CLI
- Authenticate user (`gh auth`)
- Create PRs (`gh pr create`)

### Streamlit
- Interactive dashboard for monitoring
- Real-time workflow state visualization

### Playwright
- Run UI tests via `scripts/run_ui_regression.sh`
- Generate test reports

## ⚙️ Configuration Files

### `.env`
Environment variables for:
- `GITHUB_TOKEN`: Personal access token
- `TEAMS_WEBHOOK_URL`: Teams incoming webhook

### `requirements.txt`
Added dependencies:
- `fastapi`: Web framework for orchestrator
- `uvicorn`: ASGI server
- `pydantic`: Data validation
- `requests`: HTTP client for GitHub/Teams APIs
- `python-dotenv`: Load .env files
- `pandas`: Dashboard data handling

## 🐛 Troubleshooting

### Orchestrator won't start
```bash
# Check if port 8090 is in use
lsof -i :8090

# Kill process if needed, then restart
pkill -f "uvicorn ai_workflow"
uvicorn ai_workflow.main:app --reload --port 8090
```

### GitHub API calls failing
```bash
# Verify authentication
gh auth status

# Re-authenticate if needed
gh auth login
```

### Teams not receiving escalations
```bash
# Check if webhook URL is set
echo $TEAMS_WEBHOOK_URL

# Verify Teams channel permissions
# Test webhook manually:
curl -X POST "$TEAMS_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"@type":"MessageCard","@context":"https://schema.org/extensions","summary":"Test","themeColor":"0078D4","sections":[{"activityTitle":"Test","text":"Webhook working"}]}'
```

### Tests failing in step 3 or 4
1. Check orchestrator logs for error details
2. Check dashboard for error message
3. Fix the code issue manually
4. Restart workflow (create new issue or re-trigger)

## 📞 Support

For detailed setup and troubleshooting, see [AI_WORKFLOW_SETUP.md](AI_WORKFLOW_SETUP.md).

## 🎯 Next Steps

1. **Deploy**: Follow [AI_WORKFLOW_SETUP.md](AI_WORKFLOW_SETUP.md)
2. **Test**: Trigger workflow on a test issue
3. **Monitor**: Watch dashboard during execution
4. **Iterate**: Adjust personas.py logic based on your workflow

---

**Status**: ✅ Ready to deploy  
**Last Updated**: April 19, 2026  
**Maintained By**: CompIntCalculator Team
