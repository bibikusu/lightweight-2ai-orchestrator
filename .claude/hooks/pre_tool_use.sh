#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PREFLIGHT="${REPO_ROOT}/scripts/preflight_session.sh"

if [[ ! -f "${PREFLIGHT}" ]] || [[ ! -x "${PREFLIGHT}" ]]; then
  echo "preflight_session.sh missing or not executable: ${PREFLIGHT}" >&2
  exit 1
fi

bash "${PREFLIGHT}" "${CLAUDE_SESSION_ID:-}"
