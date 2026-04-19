#!/usr/bin/env bash
# Session 投入前 preflight
# Usage: bash scripts/preflight_session.sh <session_id>
# Example: bash scripts/preflight_session.sh session-138
#
# Exit codes: 0 = all checks passed, 1 = one or more checks failed.

set +e
SESSION_ID="${1:-}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

WORKTREE_OK=1
BRANCH_OK=1
VENV_OK=1
SESSION_OK=1

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
    WORKTREE_OK=0
fi

echo ""
echo -e "${BLUE}[2/5] branch sync${NC}"
git fetch origin 2>/dev/null
if ! git rev-parse --verify origin/main >/dev/null 2>&1; then
    echo "  ahead: n/a, behind: n/a"
    echo -e "  ${RED}NG cannot resolve origin/main (remote/sync)${NC}"
    BRANCH_OK=0
    AHEAD=""
    BEHIND=""
else
    AHEAD=$(git rev-list --count origin/main..HEAD 2>/dev/null | tr -d ' ')
    BEHIND=$(git rev-list --count HEAD..origin/main 2>/dev/null | tr -d ' ')
    echo "  ahead: ${AHEAD:-?}, behind: ${BEHIND:-?}"
    if [ "${AHEAD:-0}" = "0" ] && [ "${BEHIND:-0}" = "0" ]; then
        echo -e "  ${GREEN}OK in sync with origin/main${NC}"
    else
        echo -e "  ${YELLOW}WARN not in sync${NC}"
        BRANCH_OK=0
    fi
fi

echo ""
echo -e "${BLUE}[3/5] venv health${NC}"
if [ -x ".venv/bin/python" ]; then
    if ! .venv/bin/python --version >/dev/null 2>&1; then
        echo -e "  ${RED}NG .venv/bin/python not runnable${NC}"
        VENV_OK=0
    else
        PY_VER=$(.venv/bin/python --version 2>&1)
        echo -e "  ${GREEN}OK .venv/bin/python: $PY_VER${NC}"
    fi
else
    echo -e "  ${RED}NG .venv/bin/python not executable${NC}"
    VENV_OK=0
fi

echo ""
echo -e "${BLUE}[4/5] recent commits${NC}"
git log --oneline -5

JSON_FILE=""
YAML_FILE=""
echo ""
echo -e "${BLUE}[5/5] session file check${NC}"
if [ -n "$SESSION_ID" ]; then
    JSON_FILE="docs/sessions/${SESSION_ID}.json"
    YAML_FILE="docs/acceptance/${SESSION_ID}.yaml"
    if [ -f "$JSON_FILE" ]; then
        echo -e "  ${YELLOW}EXISTS $JSON_FILE${NC}"
    else
        echo -e "  ${RED}NG missing $JSON_FILE${NC}"
        SESSION_OK=0
    fi
    if [ -f "$YAML_FILE" ]; then
        echo -e "  ${YELLOW}EXISTS $YAML_FILE${NC}"
    else
        echo -e "  ${RED}NG missing $YAML_FILE${NC}"
        SESSION_OK=0
    fi
else
    echo "  (session_id not specified)"
fi

echo ""
echo -e "${BLUE}[SUMMARY]${NC}"
WT_MSG="OK"; [ "$WORKTREE_OK" = "1" ] || WT_MSG="NG"
BR_MSG="OK"; [ "$BRANCH_OK" = "1" ] || BR_MSG="NG"
VE_MSG="OK"; [ "$VENV_OK" = "1" ] || VE_MSG="NG"
SE_MSG="OK"
if [ -n "$SESSION_ID" ]; then
    [ "$SESSION_OK" = "1" ] || SE_MSG="NG"
else
    SE_MSG="(n/a)"
fi
echo "  worktree:        $WT_MSG"
echo "  branch sync:     $BR_MSG"
echo "  venv:            $VE_MSG"
echo "  session files:   $SE_MSG"

PREFLIGHT_OK=1
if [ "$WORKTREE_OK" != "1" ] || [ "$BRANCH_OK" != "1" ] || [ "$VENV_OK" != "1" ]; then
    PREFLIGHT_OK=0
fi
if [ -n "$SESSION_ID" ] && [ "$SESSION_OK" != "1" ]; then
    PREFLIGHT_OK=0
fi

echo ""
if [ "$PREFLIGHT_OK" = "1" ]; then
    echo -e "  ${GREEN}OVERALL: OK (exit 0)${NC}"
else
    echo -e "  ${RED}OVERALL: NG (exit 1)${NC}"
fi
echo "=============================================="

if [ "$PREFLIGHT_OK" = "1" ]; then
    exit 0
else
    exit 1
fi
