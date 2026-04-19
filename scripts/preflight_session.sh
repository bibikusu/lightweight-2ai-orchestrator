#!/usr/bin/env bash
# Session 投入前 preflight
# Usage: bash scripts/preflight_session.sh <session_id>
# Example: bash scripts/preflight_session.sh session-138

set +e
SESSION_ID="${1:-}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "=============================================="
echo "  Session preflight for: ${SESSION_ID:-<none>}"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="

echo ""
echo -e "${BLUE}[1/5] worktree status${NC}"
DIRTY=$(git status --short | wc -l | tr -d ' ')
if [ "$DIRTY" = "0" ]; then
    echo -e "  ${GREEN}OK clean${NC}"
else
    echo -e "  ${RED}NG dirty ($DIRTY files)${NC}"
    git status --short | head -10
fi

echo ""
echo -e "${BLUE}[2/5] branch sync${NC}"
git fetch origin 2>/dev/null
AHEAD=$(git rev-list --count origin/main..HEAD 2>/dev/null)
BEHIND=$(git rev-list --count HEAD..origin/main 2>/dev/null)
echo "  ahead: $AHEAD, behind: $BEHIND"
if [ "$AHEAD" = "0" ] && [ "$BEHIND" = "0" ]; then
    echo -e "  ${GREEN}OK in sync with origin/main${NC}"
else
    echo -e "  ${YELLOW}WARN not in sync${NC}"
fi

echo ""
echo -e "${BLUE}[3/5] venv health${NC}"
if [ -x ".venv/bin/python" ]; then
    PY_VER=$(.venv/bin/python --version 2>&1)
    echo -e "  ${GREEN}OK .venv/bin/python: $PY_VER${NC}"
else
    echo -e "  ${RED}NG .venv/bin/python not executable${NC}"
fi

echo ""
echo -e "${BLUE}[4/5] recent commits${NC}"
git log --oneline -5

echo ""
echo -e "${BLUE}[5/5] session file check${NC}"
if [ -n "$SESSION_ID" ]; then
    JSON_FILE="docs/sessions/${SESSION_ID}.json"
    YAML_FILE="docs/acceptance/${SESSION_ID}.yaml"
    if [ -f "$JSON_FILE" ]; then
        echo -e "  ${YELLOW}EXISTS $JSON_FILE${NC}"
    else
        echo "  (not placed yet) $JSON_FILE"
    fi
    if [ -f "$YAML_FILE" ]; then
        echo -e "  ${YELLOW}EXISTS $YAML_FILE${NC}"
    else
        echo "  (not placed yet) $YAML_FILE"
    fi
else
    echo "  (session_id not specified)"
fi

echo ""
echo "=============================================="
