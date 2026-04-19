#!/usr/bin/env bash

# AI Workflow Setup Validation Script
# Verifies that all required dependencies and configurations are in place

set -u

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASSED=0
FAILED=0

check_python_version() {
    echo -n "Checking Python version... "
    if python3 --version | grep -q "Python 3\.[0-9]*" ; then
        echo -e "${GREEN}✓${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} Python 3.10+ required"
        ((FAILED++))
        return 1
    fi
}

check_package() {
    local package=$1
    echo -n "Checking $package... "
    if python3 -c "import $package" 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} Install with: pip3 install -r requirements.txt"
        ((FAILED++))
        return 1
    fi
}

check_github_auth() {
    echo -n "Checking GitHub authentication... "
    if gh auth status >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠${NC} Run: gh auth login"
        ((FAILED++))
        return 1
    fi
}

check_env_file() {
    echo -n "Checking .env file... "
    if [ -f ".env" ]; then
        if grep -q "GITHUB_TOKEN" .env && grep -q "TEAMS_WEBHOOK_URL" .env; then
            echo -e "${GREEN}✓${NC}"
            ((PASSED++))
            return 0
        else
            echo -e "${YELLOW}⚠${NC} .env file exists but may be incomplete"
            ((FAILED++))
            return 1
        fi
    else
        echo -e "${YELLOW}⚠${NC} No .env file. Copy from .env.example"
        ((FAILED++))
        return 1
    fi
}

check_directory_structure() {
    echo -n "Checking directory structure... "
    dirs_ok=true
    for dir in ".github/agents" ".github/instructions" ".github/prompts" "ai_workflow" ".workflow/state"; do
        if [ ! -d "$dir" ]; then
            echo -e "${RED}✗${NC} Missing $dir/"
            dirs_ok=false
        fi
    done
    
    if $dirs_ok; then
        echo -e "${GREEN}✓${NC}"
        ((PASSED++))
        return 0
    else
        ((FAILED++))
        return 1
    fi
}

check_files() {
    echo -n "Checking required files... "
    files_ok=true
    for file in ".github/agents/issue-workflow.agent.md" ".github/instructions/workflow-trigger.instructions.md" "ai_workflow/main.py" "workflow_dashboard.py"; do
        if [ ! -f "$file" ]; then
            echo -e "${RED}✗${NC} Missing $file"
            files_ok=false
        fi
    done
    
    if $files_ok; then
        echo -e "${GREEN}✓${NC}"
        ((PASSED++))
        return 0
    else
        ((FAILED++))
        return 1
    fi
}

main() {
    echo ""
    echo "🤖 AI Workflow Setup Validation"
    echo "================================"
    echo ""

    check_python_version
    check_package "streamlit"
    check_package "fastapi"
    check_package "pydantic"
    check_package "requests"
    check_package "pandas"
    check_github_auth
    check_env_file
    check_directory_structure
    check_files

    echo ""
    echo "Results: ${GREEN}$PASSED passed${NC}, ${RED}$FAILED failed${NC}"
    echo ""

    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ All checks passed!${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Start orchestrator: uvicorn ai_workflow.main:app --reload --port 8090"
        echo "2. (Optional) Start dashboard: streamlit run workflow_dashboard.py"
        echo "3. In Copilot Chat, say: Start work on git issue #1"
        echo ""
        exit 0
    else
        echo -e "${RED}✗ Some checks failed. See above for details.${NC}"
        exit 1
    fi
}

main
