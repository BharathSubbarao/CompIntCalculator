#!/usr/bin/env zsh
# setup-playwright.sh - Setup script for Playwright testing environment

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Compound Interest Calculator - Playwright Setup${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js is not installed${NC}"
    echo ""
    echo "Please install Node.js first. Choose one option:"
    echo ""
    echo "1. Using Homebrew:"
    echo "   ${YELLOW}brew install node${NC}"
    echo ""
    echo "2. Using nvm (Node Version Manager):"
    echo "   ${YELLOW}curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash${NC}"
    echo "   ${YELLOW}source ~/.zshrc${NC}"
    echo "   ${YELLOW}nvm install 20${NC}"
    echo ""
    echo "3. Download from https://nodejs.org"
    echo ""
    exit 1
fi

NODE_VERSION=$(node --version)
NPM_VERSION=$(npm --version)

echo -e "${GREEN}✓ Node.js ${NODE_VERSION} detected${NC}"
echo -e "${GREEN}✓ npm ${NPM_VERSION} detected${NC}"

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo -e "${RED}✗ app.py not found. Please run this script from the project root.${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 1: Installing Playwright dependencies...${NC}"
npm install 2>&1 | grep -E "^added|^up to date" || true

# Install browser binaries
if command -v ./node_modules/.bin/playwright &> /dev/null; then
    echo ""
    echo -e "${YELLOW}Step 2: Installing Playwright browser binaries...${NC}"
    ./node_modules/.bin/playwright install chromium 2>&1 | tail -5 || echo -e "${YELLOW}Browser binaries already installed${NC}"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "You can now run Playwright tests with:"
echo ""
echo -e "${YELLOW}# Run all tests (Chromium only)${NC}"
echo "  ./node_modules/.bin/playwright test"
echo ""
echo -e "${YELLOW}# Run specific test file${NC}"
echo "  ./node_modules/.bin/playwright test ui-tests/regression/positive/"
echo ""
echo -e "${YELLOW}# Run tests in headed mode (see browser)${NC}"
echo "  ./node_modules/.bin/playwright test --headed"
echo ""
echo -e "${YELLOW}# View HTML report${NC}"
echo "  ./node_modules/.bin/playwright show-report"
echo ""
echo -e "${CYAN}For more details, see: .github/PLAYWRIGHT_SETUP.md${NC}"
