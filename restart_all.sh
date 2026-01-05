#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# TEAM82 - RESTART ALL PIPELINES (Quick mode - no preprocessing)
# ═══════════════════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Just call start_all.sh with quick mode
exec "$SCRIPT_DIR/start_all.sh" quick
