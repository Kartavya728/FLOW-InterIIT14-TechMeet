#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# TEAM82 - MASTER ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════
# Starts both Fraud-Detection and Targeted-Calling pipelines + Frontend
#
# Usage:
#   ./start_all.sh         - Start everything (both pipelines + frontend)
#   ./start_all.sh quick   - Quick restart (skip preprocessing)
# ═══════════════════════════════════════════════════════════════════════════

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_banner() {
    echo -e "${MAGENTA}"
    echo "╔═══════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                           ║"
    echo "║   ████████╗███████╗ █████╗ ███╗   ███╗ █████╗ ██████╗                     ║"
    echo "║      ██╔══╝██╔════╝██╔══██╗████╗ ████║██╔══██╗╚════██╗                    ║"
    echo "║      ██║   █████╗  ███████║██╔████╔██║╠█████╔╝ █████╔╝                    ║"
    echo "║      ██║   ██╔══╝  ██╔══██║██║╚██╔╝██║██╔══██╗██╔═══╝                     ║"
    echo "║      ██║   ███████╗██║  ██║██║ ╚═╝ ██║╚█████╔╝███████╗                    ║"
    echo "║      ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚════╝ ╚══════╝                    ║"
    echo "║                                                                           ║"
    echo "║   FRAUD DETECTION + TARGETED CALLING PIPELINE                             ║"
    echo "║                                                                           ║"
    echo "╚═══════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')]${NC} ${GREEN}$1${NC}"
}

print_header() {
    echo -e "${CYAN}"
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo "   $1"
    echo "═══════════════════════════════════════════════════════════════════════════"
    echo -e "${NC}"
}

# Determine mode
MODE="${1:-start}"
if [ "$MODE" == "quick" ]; then
    FRAUD_CMD="restart"
    TARGET_CMD="restart"
else
    FRAUD_CMD="start"
    TARGET_CMD="start"
fi

print_banner

# ═══════════════════════════════════════════════════════════════════════════
# STEP 1: Start Fraud-Detection Pipeline
# ═══════════════════════════════════════════════════════════════════════════
print_header "STARTING FRAUD-DETECTION PIPELINE"

cd "$SCRIPT_DIR/Fraud-Detection"
if [ -f "./pipeline.sh" ]; then
    ./pipeline.sh $FRAUD_CMD
else
    echo -e "${RED}Error: Fraud-Detection/pipeline.sh not found${NC}"
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════════════
# STEP 2: Start Targeted-Calling Pipeline
# ═══════════════════════════════════════════════════════════════════════════
print_header "STARTING TARGETED-CALLING PIPELINE"

cd "$SCRIPT_DIR/Targeted-Calling"
if [ -f "./pipeline.sh" ]; then
    ./pipeline.sh $TARGET_CMD
else
    echo -e "${RED}Error: Targeted-Calling/pipeline.sh not found${NC}"
    exit 1
fi

# ═══════════════════════════════════════════════════════════════════════════
# STEP 3: Start Frontend
# ═══════════════════════════════════════════════════════════════════════════
print_header "STARTING FRONTEND"

cd "$SCRIPT_DIR/Targeted-Calling/Frontend"
print_step "Installing frontend dependencies..."
npm install --silent 2>/dev/null || npm install

print_step "Starting frontend development server..."
# Run frontend in background
npm run dev &
FRONTEND_PID=$!
echo $FRONTEND_PID > "$SCRIPT_DIR/.frontend.pid"

sleep 3

# ═══════════════════════════════════════════════════════════════════════════
# DONE!
# ═══════════════════════════════════════════════════════════════════════════
echo ""
print_header "ALL SYSTEMS RUNNING!"
echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                         ACCESS POINTS                                     ║"
echo "╠═══════════════════════════════════════════════════════════════════════════╣"
echo "║                                                                           ║"
echo "║   🎨 FRONTEND (Main Dashboard)                                           ║"
echo "║      → http://localhost:5173                                              ║"
echo "║                                                                           ║"
echo "║   📊 GRAFANA DASHBOARDS                                                   ║"
echo "║      → Fraud-Detection:    http://localhost:3000  (admin/admin)           ║"
echo "║      → Targeted-Calling:   http://localhost:3001  (admin/admin)           ║"
echo "║                                                                           ║"
echo "║   🔧 PROMETHEUS METRICS                                                   ║"
echo "║      → Fraud-Detection:    http://localhost:9090                          ║"
echo "║      → Targeted-Calling:   http://localhost:9095                          ║"
echo "║                                                                           ║"
echo "║   🌐 API BACKENDS                                                         ║"
echo "║      → Fraud-Detection:    http://localhost:8000                          ║"
echo "║      → Targeted-Calling:   http://localhost:5001                          ║"
echo "║                                                                           ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "To stop everything: ./stop_all.sh"
echo ""
