#!/usr/bin/env bash
set -euo pipefail

OWNER="${1:-tkhjp}"
REPOSITORY="${2:-copilot-agent-knowledge-demo}"
BRANCH="${3:-develop}"
REMOTE_URL="https://github.com/${OWNER}/${REPOSITORY}.git"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required" >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree must be clean before publishing." >&2
  exit 1
fi

current_branch="$(git branch --show-current)"
if [[ "$current_branch" != "$BRANCH" ]]; then
  git branch -M "$BRANCH"
fi

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE_URL"
else
  git remote add origin "$REMOTE_URL"
fi

echo "Publishing to ${REMOTE_URL} on ${BRANCH}..."
git push --set-upstream origin "$BRANCH"
