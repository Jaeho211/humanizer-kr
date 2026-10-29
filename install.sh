#!/usr/bin/env bash
# Install the same skill bundle into 4 agent runtimes. No downloads.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$ROOT/skills/humanizer-kr"
SCOPE="user"
PROJECT="$(pwd)"
AGENTS="omp,agy,codex,claude"
MODE="copy"
FORCE=0
DRY=0

usage() {
  cat <<'USAGE'
Usage: bash install.sh [--scope user|project] [--project DIR] [--agents omp,agy,codex,claude]
                       [--copy|--link] [--force] [--dry-run]
Default: install or update all four agents in user scope, keeping backups.
Agents: omp, agy (CLI only), codex, claude, all.
Examples:
  bash install.sh --dry-run
  bash install.sh --scope project --project "$PWD" --agents all
  bash install.sh --force --agents omp,agy
Note: changed installations are backed up as *.bak.TIMESTAMP; --force also re-installs unchanged ones.
USAGE
}

while (($#)); do
  case "$1" in
    --scope) SCOPE="${2:?}"; shift 2 ;;
    --project) PROJECT="${2:?}"; shift 2 ;;
    --agents) AGENTS="${2:?}"; shift 2 ;;
    --copy) MODE="copy"; shift ;;
    --link) MODE="link"; shift ;;
    --force) FORCE=1; shift ;;
    --dry-run) DRY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
done
[[ "$SCOPE" == user || "$SCOPE" == project ]] || { echo "--scope: user or project" >&2; exit 2; }
[[ -f "$SOURCE/SKILL.md" ]] || { echo "Skill not found: $SOURCE" >&2; exit 2; }

# The destinations below reflect agent skill paths as of 2026-10.
if [[ "$SCOPE" == project ]]; then
  PROJECT="$(cd "$PROJECT" && pwd)"
fi

get_targets() {
  local agent="$1"
  if [[ "$SCOPE" == user ]]; then
    case "$agent" in
      omp) printf '%s\n' "${OMP_HOME:-$HOME/.omp/agent}/skills/humanizer-kr" ;;
      agy) printf '%s\n' "${AGY_CLI_HOME:-$HOME/.gemini/antigravity-cli}/skills/humanizer-kr" ;;
      codex) printf '%s\n' "${CODEX_HOME:-$HOME/.codex}/skills/humanizer-kr" ;;
      claude) printf '%s\n' "${CLAUDE_HOME:-$HOME/.claude}/skills/humanizer-kr" ;;
      *) echo "Unknown agent: $agent" >&2; exit 2 ;;
    esac
  else
    case "$agent" in
      omp) printf '%s\n' "$PROJECT/.omp/skills/humanizer-kr" ;;
      agy|codex) printf '%s\n' "$PROJECT/.agents/skills/humanizer-kr" ;;
      claude) printf '%s\n' "$PROJECT/.claude/skills/humanizer-kr" ;;
      *) echo "Unknown agent: $agent" >&2; exit 2 ;;
    esac
  fi
}

if [[ "$AGENTS" == all ]]; then AGENTS="omp,agy,codex,claude"; fi
IFS=',' read -r -a agent_list <<< "$AGENTS"
declare -A seen=()
targets=()
for agent in "${agent_list[@]}"; do
  case "$agent" in omp|agy|codex|claude) ;; *) echo "Invalid agent: $agent" >&2; exit 2 ;; esac
  while IFS= read -r path; do
    [[ -n "${seen[$path]:-}" ]] && continue
    seen["$path"]=1
    targets+=("$path")
  done < <(get_targets "$agent")
done

stamp="$(date +%Y%m%d%H%M%S)"
for target in "${targets[@]}"; do
  if [[ -e "$target" || -L "$target" ]]; then
    if [[ "$FORCE" -ne 1 ]]; then
      if [[ "$MODE" == copy && -d "$target" && ! -L "$target" ]] && diff -qr "$SOURCE" "$target" >/dev/null; then
        echo "UP-TO-DATE: $target"
        continue
      fi
      if [[ "$MODE" == link && -L "$target" && "$(readlink "$target")" == "$SOURCE" ]]; then
        echo "UP-TO-DATE: $target"
        continue
      fi
    fi
    backup="$target.bak.$stamp"
    suffix=1
    while [[ -e "$backup" || -L "$backup" ]]; do
      backup="$target.bak.$stamp.$suffix"
      suffix=$((suffix + 1))
    done
    echo "BACKUP $target -> $backup"
    if [[ "$DRY" -eq 0 ]]; then mv "$target" "$backup"; fi
  fi
  echo "INSTALL ($MODE): $target"
  if [[ "$DRY" -eq 1 ]]; then continue; fi
  mkdir -p "$(dirname "$target")"
  if [[ "$MODE" == link ]]; then
    ln -s "$SOURCE" "$target"
  else
    cp -R "$SOURCE" "$target"
  fi
done
if [[ "$DRY" -eq 1 ]]; then echo "Dry run: no files changed."; fi
echo "완료. 실행 중인 에이전트를 새로 열어 스킬 검색을 확인하세요."
