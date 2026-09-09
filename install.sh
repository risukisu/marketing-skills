#!/usr/bin/env bash
# Link (or copy) every skill in this repo into ~/.claude/skills so Claude Code can load it.
#
# Claude Code discovers skills one folder deep under ~/.claude/skills. This repo keeps skills in
# skills/<Category>/.../<skill>/SKILL.md, so each skill gets a symlink (default) or a copy (--copy)
# at ~/.claude/skills/<skill>. Sub-agents shipped with the SEO suite are copied to ~/.claude/agents.
# Re-run after pulling to pick up new skills. Safe to re-run.
#
#   ./install.sh            symlink skills, copy agents
#   ./install.sh --copy     copy skills instead of linking
#   ./install.sh --uninstall

set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_HOME="${HOME}/.claude/skills"
AGENTS_HOME="${HOME}/.claude/agents"
MODE="link"; UNINSTALL=0
for arg in "$@"; do
  case "$arg" in
    --copy) MODE="copy" ;;
    --uninstall) UNINSTALL=1 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done
mkdir -p "${SKILLS_HOME}" "${AGENTS_HOME}"

# Skip runtime folders (the SEO suite's Python venv ships third-party SKILL.md files).
mapfile -t SKILL_DIRS < <(find "${REPO}/skills" \( -name '.venv*' -o -name ms-playwright -o -name node_modules -o -name __pycache__ -o -name .git \) -prune -o -name SKILL.md -type f -print | xargs -I{} dirname {} | sort -u)
AGENTS_DIR="${REPO}/skills/SEO/claude-seo/agents"

if [ "${UNINSTALL}" -eq 1 ]; then
  for d in "${SKILL_DIRS[@]}"; do
    name="$(basename "$d")"; target="${SKILLS_HOME}/${name}"
    if [ -L "$target" ]; then rm "$target"; echo "unlinked ${name}"
    elif [ -d "$target" ] && [ "$MODE" = "copy" ]; then rm -rf "$target"; echo "removed copy ${name}"
    elif [ -d "$target" ]; then echo "left ${name} (real folder; pass --copy to remove copies)"; fi
  done
  [ -d "${AGENTS_DIR}" ] && for a in "${AGENTS_DIR}"/*.md; do rm -f "${AGENTS_HOME}/$(basename "$a")"; done
  echo "Uninstall complete."; exit 0
fi

linked=0; skipped=0
for d in "${SKILL_DIRS[@]}"; do
  name="$(basename "$d")"; target="${SKILLS_HOME}/${name}"
  if [ -L "$target" ]; then
    [ "$(readlink -f "$target")" = "$(readlink -f "$d")" ] && { skipped=$((skipped+1)); continue; }
    rm "$target"
  elif [ -e "$target" ]; then
    echo "skipping ${name}: a real folder already exists at ${target}" >&2; skipped=$((skipped+1)); continue
  fi
  if [ "$MODE" = "copy" ]; then cp -R "$d" "$target"; else ln -s "$d" "$target"; fi
  linked=$((linked+1))
done
agents=0
if [ -d "${AGENTS_DIR}" ]; then for a in "${AGENTS_DIR}"/*.md; do cp -f "$a" "${AGENTS_HOME}/"; agents=$((agents+1)); done; fi

echo "Skills: ${linked} ${MODE}ed, ${skipped} already in place. Agents: ${agents} copied."
echo "SEO suite runtime: run  \"${SKILLS_HOME}/seo/bin/claude-seo\" setup  once (creates an isolated Python environment)."
