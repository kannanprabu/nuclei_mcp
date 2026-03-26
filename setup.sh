#!/bin/bash
# =============================================================================
# nuclei_mcp - Automated Setup Script
# BSides San Diego 2026
# Tested on: macOS Tahoe, Apple Silicon M1/M2/M3/M4
# =============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "============================================="
echo "  nuclei_mcp Setup - BSides SD 2026"
echo "============================================="
echo -e "${NC}"

# ── 1. Check Python ───────────────────────────────────────────────────────────
echo -e "${BLUE}[1/4] Checking Python...${NC}"
if ! command -v python3 &>/dev/null; then
  echo -e "${RED}ERROR: python3 not found. Install from https://python.org${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Python found: $(python3 --version)${NC}"

# ── 2. Install Nuclei ─────────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}[2/4] Checking Nuclei...${NC}"

if command -v nuclei &>/dev/null; then
  echo -e "${GREEN}✓ Nuclei already installed: $(nuclei -version 2>&1 | grep 'Engine Version' | head -1)${NC}"
else
  echo -e "${YELLOW}Nuclei not found. Installing official arm64 binary...${NC}"
  echo -e "${YELLOW}NOTE: Do NOT use 'brew install nuclei' — it crashes on Apple Silicon (SIGSEGV/cgo bug)${NC}"

  ARCH=$(uname -m)
  if [[ "$ARCH" == "arm64" ]]; then
    NUCLEI_URL="https://github.com/projectdiscovery/nuclei/releases/download/v3.3.9/nuclei_3.3.9_macOS_arm64.zip"
  else
    NUCLEI_URL="https://github.com/projectdiscovery/nuclei/releases/download/v3.3.9/nuclei_3.3.9_macOS_amd64.zip"
  fi

  curl -L "$NUCLEI_URL" -o /tmp/nuclei.zip
  unzip -o /tmp/nuclei.zip -d /tmp/nuclei-bin/
  chmod +x /tmp/nuclei-bin/nuclei
  sudo mv /tmp/nuclei-bin/nuclei /usr/local/bin/nuclei

  # Remove Gatekeeper quarantine if present
  xattr -d com.apple.quarantine /usr/local/bin/nuclei 2>/dev/null || true

  echo -e "${GREEN}✓ Nuclei installed successfully${NC}"
fi

# Update nuclei and templates
echo -e "${BLUE}Updating nuclei to latest version...${NC}"
sudo nuclei -update 2>/dev/null || true
echo -e "${BLUE}Updating nuclei templates...${NC}"
nuclei -update-templates 2>/dev/null || true
echo -e "${GREEN}✓ Nuclei templates up to date${NC}"

# ── 3. Python venv + dependencies ─────────────────────────────────────────────
echo ""
echo -e "${BLUE}[3/4] Setting up Python environment...${NC}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

python3 -m venv venv
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo -e "${GREEN}✓ Python environment ready${NC}"
echo -e "${GREEN}✓ MCP library installed: $(pip show mcp | grep Version)${NC}"

# ── 4. Print Claude Desktop config ────────────────────────────────────────────
echo ""
echo -e "${BLUE}[4/4] Claude Desktop Configuration${NC}"
echo ""

PYTHON_PATH="$SCRIPT_DIR/venv/bin/python3"
SERVER_PATH="$SCRIPT_DIR/nuclei-server.py"

echo -e "${YELLOW}Add this to your Claude Desktop config:${NC}"
echo -e "${YELLOW}File: ~/Library/Application Support/Claude/claude_desktop_config.json${NC}"
echo ""
echo -e "${GREEN}"
cat << CONFIG
{
  "mcpServers": {
    "nuclei-scanner": {
      "command": "$PYTHON_PATH",
      "args": ["$SERVER_PATH"]
    }
  }
}
CONFIG
echo -e "${NC}"

echo -e "${YELLOW}If you have existing mcpServers, just add the 'nuclei-scanner' block inside.${NC}"
echo ""
echo "============================================="
echo -e "${GREEN}  Setup complete!${NC}"
echo "============================================="
echo ""
echo "Next steps:"
echo "  1. Copy the config above into claude_desktop_config.json"
echo "  2. Run: pkill -x \"Claude\" && open -a Claude"
echo "  3. In Claude Desktop, type: Run a nuclei scan on https://scanme.sh"
echo "  4. Expect 19 findings in ~7 seconds"
echo ""
