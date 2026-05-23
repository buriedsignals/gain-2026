#!/usr/bin/env bash
# data-detective installer — flat-copies the skill package into a Claude Code
# config so the orchestrator + every sub-skill registers individually.
# Override destinations with $CLAUDE_SKILLS_DIR and $CLAUDE_AGENTS_DIR.
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/data-detective" && pwd)"
DEST_SKILLS="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
DEST_AGENTS="${CLAUDE_AGENTS_DIR:-$HOME/.claude/agents}"

mkdir -p "$DEST_SKILLS" "$DEST_AGENTS"

echo "==> data-detective install"
echo "    skills → $DEST_SKILLS"
echo "    agents → $DEST_AGENTS"
echo

for d in "$SRC"/skills/*/; do
  name=$(basename "$d")
  rm -rf "$DEST_SKILLS/$name"
  cp -R "$d" "$DEST_SKILLS/$name"
  echo "    + skill  $name"
done

for f in "$SRC"/agents/*.md; do
  name=$(basename "$f")
  cp "$f" "$DEST_AGENTS/$name"
  echo "    + agent  $name"
done

echo
echo "Done. In a fresh Claude Code session, type:  /data-detective"
