#!/usr/bin/env bash
#
# run-folder.sh — batch-drive the single-file /visual-prompt skill across one
# novel series folder, one chapter file at a time, each in a FRESH agy session.
#
# This is a THIN driver: it only orchestrates I/O and re-invokes the active Agy
# model (agy -p). It NEVER generates prompts itself and NEVER calls an external
# model — every file is expanded by the real /visual-prompt pipeline. (RULE 0)
#
# Per series, the art style is detected once on the first file (skill scans the
# first chapters and picks #1), locked into <folder>/.vp-series.conf, then reused
# via --style for every later file so the whole series stays visually consistent
# and the interactive style prompt never reappears.
#
# Usage:   run-folder.sh <series-folder>
# Env:     VP_MODEL   pinned agy model        (default: "Gemini 3.1 Pro (High)")
#          VP_MUSIC   music loops per file     (default: 4)
#          VP_DRYRUN  =1 → print the agy command instead of running it (review)
#
# Resume:  a file whose <stem>_image_prompts.txt already exists is skipped, so a
#          re-run after a crash / quota reset continues where it stopped.

set -uo pipefail

MODEL="${VP_MODEL:-Gemini 3.1 Pro (High)}"
MUSIC="${VP_MUSIC:-4}"
DRYRUN="${VP_DRYRUN:-0}"

# Skill root = repo dir holding scripts/ + prompts/. agy -p inherits the launch
# CWD; we run it from here so the skill's relative paths (scripts/load_input.py,
# @prompts/*.md) resolve. Otherwise the model can't find them and may launch a
# runaway `find /home -name ...` that traverses gdrive mounts for hours.
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

die() { echo "❌ $*" >&2; exit 1; }

# kebab-case a folder name into a stable, filesystem-safe series id
slugify() {
  local s
  s=$(echo "$1" | iconv -f utf-8 -t ascii//TRANSLIT 2>/dev/null) || s="$1"
  [ -z "$s" ] && s="$1"
  echo "$s" | tr '[:upper:]' '[:lower:]' \
    | sed -e 's/[^a-z0-9]\+/-/g' -e 's/^-\+//' -e 's/-\+$//'
}

# Walk up from a directory to the nearest .vp-series.conf (shared per-novel
# config). Lets every work-split subfolder of one novel inherit the same series
# + locked style — print the path on success, non-zero if none found.
find_conf() {
  local d="$1"
  while :; do
    [ -f "$d/.vp-series.conf" ] && { echo "$d/.vp-series.conf"; return 0; }
    local parent; parent=$(dirname "$d")
    [ "$parent" = "$d" ] && return 1   # reached filesystem root
    d="$parent"
  done
}

conf_get() { sed -n "s/^$2=//p" "$1" 2>/dev/null | head -1; }

# conf_set <file> <key> <value> — idempotent key write, preserves other keys.
# Uses a truncate-write (not `sed -i`) because the config often lives on a gdrive
# FUSE mount where in-place rename (sed -i / mv) raises I/O errors.
conf_set() {
  local f="$1" k="$2" v="$3" rest=""
  [ -f "$f" ] && rest=$(grep -v "^$k=" "$f" 2>/dev/null)
  { [ -n "$rest" ] && printf '%s\n' "$rest"; printf '%s=%s\n' "$k" "$v"; } > "$f"
}

# treat a .txt as a generated OUTPUT (not an input chapter file) — skip these
is_output_file() {
  case "$1" in
    *_qa.txt|*_image_prompts.txt|*_video_prompts.txt|*_music_prompts.txt) return 0 ;;
    *) return 1 ;;
  esac
}

[ $# -eq 1 ] || die "Usage: run-folder.sh <series-folder>"
FOLDER="${1%/}"
[ -d "$FOLDER" ] || die "Không phải thư mục: $FOLDER"

# Shared per-novel config lives at the novel root (the folder that holds all the
# work-split subfolders). Find an existing one upward; else default to the input
# folder's parent so sibling subfolders of the same novel share it.
CONF=$(find_conf "$FOLDER") || CONF="$(dirname "$FOLDER")/.vp-series.conf"

# Series precedence: VP_SERIES env  >  config file  >  folder-name slug (warn).
# A whole novel split across subfolders must keep ONE series name (one bible).
SERIES="${VP_SERIES:-}"
[ -z "$SERIES" ] && SERIES=$(conf_get "$CONF" series)
if [ -z "$SERIES" ]; then
  SERIES=$(slugify "$(basename "$FOLDER")")
  echo "⚠ Chưa có series config — tạm dùng slug folder: '$SERIES'." >&2
  echo "  Đặt VP_SERIES='<tên-bộ>' hoặc tạo $CONF với dòng 'series=<tên-bộ>' để các subfolder dùng chung 1 bible." >&2
fi
[ -n "$SERIES" ] || die "Không suy ra được series name từ: $FOLDER"
conf_set "$CONF" series "$SERIES"

# Pre-flight: refuse to run if the pinned model name no longer exists in agy.
# Fails loud (instead of silently using a wrong/weaker default) when Google
# renames or retires a model — change VP_MODEL and re-run.
if [ "$DRYRUN" != "1" ]; then
  agy models 2>/dev/null | grep -qF "$MODEL" || {
    echo "❌ Model '$MODEL' không còn trong agy. Danh sách hiện có:" >&2
    agy models >&2
    die "Sửa VP_MODEL rồi chạy lại (vd: VP_MODEL='Gemini 4 Pro (High)' $0 '$FOLDER')."
  }
fi

# Load a previously locked style for this series from the shared config, if any.
STYLE=$(conf_get "$CONF" style)

# Collect input chapter files in chapter order (filenames sort lexically:
# _0001_0010, _0011_0020, ...). Output .txt files are excluded.
mapfile -t FILES < <(find "$FOLDER" -maxdepth 1 -type f -name '*.txt' | sort)
INPUTS=()
for f in "${FILES[@]}"; do is_output_file "$f" || INPUTS+=("$f"); done
[ ${#INPUTS[@]} -gt 0 ] || die "Không có file truyện .txt nào trong: $FOLDER"

echo "▶ Bộ: $SERIES | model: $MODEL | music: $MUSIC | files: ${#INPUTS[@]} | style: ${STYLE:-(auto file đầu)}"

total=${#INPUTS[@]}; idx=0
for f in "${INPUTS[@]}"; do
  idx=$((idx + 1))
  stem="${f%.txt}"
  tag="[$SERIES] $idx/$total $(basename "$f")"

  if [ -f "${stem}_image_prompts.txt" ]; then
    echo "⏭  $tag — đã có output, skip"
    continue
  fi

  # Build the skill invocation. Style flag only when already locked for the series.
  cmd="/visual-prompt:visual-prompt '$f' --series '$SERIES' --music $MUSIC"
  [ -n "$STYLE" ] && cmd="$cmd --style $STYLE"

  echo "▶ $tag — đang chạy${STYLE:+ (style: $STYLE)}"

  if [ "$DRYRUN" = "1" ]; then
    echo "   DRYRUN: (cd \"$SKILL_DIR\" && agy -p \"$cmd\" --model \"$MODEL\" --print-timeout 3h --dangerously-skip-permissions --add-dir \"$SKILL_DIR\" --add-dir \"$FOLDER\")"
    # simulate style-lock on the first file so dry-run shows later files inheriting it
    [ -z "$STYLE" ] && { STYLE="donghua-xianxia"; echo "   DRYRUN: (giả lập) khoá style=$STYLE → $CONF"; }
    continue
  fi

  log=$(mktemp)
  ( cd "$SKILL_DIR" && agy -p "$cmd" \
      --model "$MODEL" \
      --print-timeout 3h \
      --dangerously-skip-permissions \
      --add-dir "$SKILL_DIR" \
      --add-dir "$FOLDER" ) 2>&1 | tee "$log"

  # First file just established the style — capture it and lock for the series.
  # Read it from the materialized .work/active-style.md (deterministic: its first
  # line is "### <id> — ...") rather than grepping the model's free-text stdout.
  if [ -z "$STYLE" ]; then
    picked=$(sed -n 's/^### \([a-z0-9-][a-z0-9-]*\).*/\1/p' "$FOLDER/.work/active-style.md" 2>/dev/null | head -1)
    if [ -n "$picked" ]; then
      STYLE="$picked"
      conf_set "$CONF" style "$STYLE"
      echo "🔒 $tag — khoá style cho bộ: $STYLE → $CONF"
    else
      echo "⚠ $tag — không bắt được 'Style:' từ output; file sau sẽ tự detect lại" >&2
    fi
  fi
  rm -f "$log"

  # Verify the run actually produced its core artifact before moving on.
  if [ ! -s "${stem}_image_prompts.txt" ]; then
    die "$tag — thiếu/rỗng ${stem}_image_prompts.txt. Dừng ở file này (chạy lại để resume)."
  fi

  # Integrity gate: the legit pipeline never writes .py into .work, so any .py
  # there means the model bypassed the LLM expander with its own generator —
  # surface it. Then deterministically normalize every character anchor against
  # the series bible so a drifted run can't ship an inconsistent protagonist.
  if ls "$FOLDER"/.work/*.py >/dev/null 2>&1; then
    echo "⚠ $tag — phát hiện script tự chế trong .work (model bypass expander) — kiểm/sửa anchor:"
  fi
  bible_file="$HOME/.gemini/bibles/$SERIES.md"
  for kind in image video; do
    pf="${stem}_${kind}_prompts.txt"
    [ -s "$pf" ] || continue
    [ -f "$bible_file" ] && python3 "$SKILL_DIR/scripts/check_anchor_consistency.py" \
      --bible "$bible_file" --output "$pf" --fix
    # Content-safety gate: strip brand/IP/likeness/gore/sexual + ban live-action
    # video; religion is WARN-only. WARN does not halt the batch.
    python3 "$SKILL_DIR/scripts/check_content_safety.py" \
      --blocklist "$SKILL_DIR/references/blocklist-content-safety.md" \
      --output "$pf" --fix || true
  done
  echo "✅ $tag — xong"
done

echo "✔ Hoàn tất bộ: $SERIES"
