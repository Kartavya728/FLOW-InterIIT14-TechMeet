#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# TEAM82 - STOP ALL PIPELINES
# ═══════════════════════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_header() {
    echo -e "${CYAN}"
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo "   $1"
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo -e "${NC}"
}

print_header "STOPPING ALL PIPELINES"

# Stop Frontend
echo -e "${GREEN}[1/3]${NC} Stopping Frontend..."
if [ -f "$SCRIPT_DIR/.frontend.pid" ]; then
    FRONTEND_PID=$(cat "$SCRIPT_DIR/.frontend.pid")
    kill $FRONTEND_PID 2>/dev/null || true
    rm -f "$SCRIPT_DIR/.frontend.pid"
fi
# Also kill any vite dev servers
pkill -f "vite" 2>/dev/null || true

# Stop Targeted-Calling Pipeline
echo -e "${GREEN}[2/3]${NC} Stopping Targeted-Calling Pipeline..."
cd "$SCRIPT_DIR/Targeted-Calling"
if [ -f "./pipeline.sh" ]; then
    ./pipeline.sh stop 2>/dev/null || true
fi

# Stop Fraud-Detection Pipeline
echo -e "${GREEN}[3/3]${NC} Stopping Fraud-Detection Pipeline..."
cd "$SCRIPT_DIR/Fraud-Detection"
if [ -f "./pipeline.sh" ]; then
    ./pipeline.sh stop 2>/dev/null || true
fi

print_header "ALL PIPELINES STOPPED"
echo -e "${GREEN}All containers and services have been stopped.${NC}"
echo ""
