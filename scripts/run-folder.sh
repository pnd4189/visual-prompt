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
#          VP_LOCAL   local workdir base       (default: $HOME/.cache/vp-run-<series>)
#
# Local-run strategy: the skill creates .work and writes its outputs next to the
# INPUT file. Running directly on a gdrive/rclone FUSE mount breaks subagent writes
# (permission timeouts) and stalls on I/O, which pushes the model into bypassing the
# pipeline (external CLI calls, template fallback). So each file is copied to a fresh
# LOCAL dir, the whole pipeline runs there, and only the final _*.txt outputs are
# copied back to the gdrive folder.
#
# Resume:  file-level — a file whose <stem>_image_prompts.txt already exists in the
#          gdrive folder is skipped. Each file runs in a fresh local workdir, so a
#          re-run after a crash restarts the UNFINISHED file cleanly while finished
#          files stay skipped.

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

# Base dir for per-file local workdirs (keeps the pipeline off the gdrive FUSE
# mount). Default under $HOME/.cache, NOT /tmp — /tmp is cleared on reboot, and
# an overnight reboot wiped a 6-file batch's local workdirs mid-run. A persistent
# base survives reboot; each file still gets a fresh subdir (rm -rf per file).
LOCAL_BASE="${VP_LOCAL:-$HOME/.cache/vp-run-$SERIES}"

# Grant agy read access to the series bibles dir so scene-expansion subagents can
# read ~/.gemini/bibles/<series>.md directly. Without this, the bible path is
# outside --add-dir, subagents can't read it, fabricate generic appearance, and
# the model restarts expansion mid-run to fix it — that restart makes the last
# subagent lag and the model yields its turn before assemble (agy -p one-shot
# exits), so no output ships. Empty if the dir is absent (per-file bible mode).
BIBLES_DIR="$HOME/.gemini/bibles"
BIBLES_ADD=""
[ -d "$BIBLES_DIR" ] && BIBLES_ADD="--add-dir $BIBLES_DIR"

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

  # Run on LOCAL disk, not gdrive. The skill creates .work + writes its outputs next
  # to the INPUT file; copying the input into a fresh local dir keeps all that churn
  # off the gdrive FUSE mount (which breaks subagent writes and stalls on I/O). Fresh
  # dir per file → no cross-file scratch leakage. Pre-create .work so the pipeline's
  # `> .work/chapters.json` (STEP 1) has its dir. Outputs get copied back after.
  local_dir="$LOCAL_BASE/$(basename "$stem")"
  local_in="$local_dir/$(basename "$f")"
  local_stem="${local_in%.txt}"
  if [ "$DRYRUN" = "1" ]; then
    echo "   DRYRUN: rm -rf + mkdir -p \"$local_dir/.work\"; cp input + file chương-trước → local; chạy local; copy _*.txt về \"$FOLDER\""
  else
    rm -rf "$local_dir" && mkdir -p "$local_dir/.work"
    cp "$f" "$local_in" || die "$tag — không copy được input sang local dir $local_dir"
    # Pre-stage the skill's prompts/ + references/ into the local workdir so any
    # subagent whose CWD is local_dir resolves `@prompts/*.md` / `@references/*.md`
    # via a relative path instead of falling back to `find /home/dung` — which
    # recurses into the gdrive FUSE mount and stalls for hours (see header note).
    cp -r "$SKILL_DIR/prompts" "$local_dir/prompts" 2>/dev/null || true
    cp -r "$SKILL_DIR/references" "$local_dir/references" 2>/dev/null || true
    # STEP 2 continuity needs the file holding the PREVIOUS chapter, which may live
    # in a sibling done-folder (e.g. "2. ĐÃ QA/"). The in-pipeline check only sees
    # the local dir, so locate that predecessor here using the FULL gdrive folder
    # context (where it actually lives) and copy just that one file in.
    # `timeout 60` bounds the broad-scan fallback inside the script: if the
    # previous chapter isn't in the input folder (rare) the fallback lists
    # sibling subdirs on the gdrive FUSE mount, which can stall in
    # request_wait_answer for hours. A timeout here lets the batch proceed
    # without a continuity excerpt (the skill's own STEP 1.25 still runs).
    prev_path=$(timeout 60 python3 "$SKILL_DIR/scripts/check_previous_continuity.py" "$f" 2>/dev/null \
      | python3 -c "import json,sys; print(json.load(sys.stdin).get('previous_path','') or '')" 2>/dev/null)
    if [ -n "$prev_path" ] && [ -f "$prev_path" ]; then
      cp "$prev_path" "$local_dir/$(basename "$prev_path")" \
        && echo "   continuity: đã copy file chương-trước $(basename "$prev_path") → local"
      # Also stage the prev under its RAW .txt name (strip `_qa`) so the model's
      # STEP 2 continuity search finds the previous chapter. The skill's own
      # check_previous_continuity.py finds the _qa.txt fine, but the model
      # sometimes improvises a raw-`*_vi.txt`-only search and misses a `_qa.txt`
      # sibling — this happens at a batch boundary where the previous file was
      # already QA'd + moved to a done-folder (so only its _qa.txt is available).
      # The raw-named copy contains the same Chương N-1 text, just under a name
      # the improvised search looks at. No-op when prev is already a raw .txt.
      prev_raw=$(basename "$prev_path" | sed 's/_qa\.txt$/.txt/')
      [ "$prev_raw" != "$(basename "$prev_path")" ] \
        && cp "$prev_path" "$local_dir/$prev_raw" 2>/dev/null || true
    else
      echo "   ⚠ continuity: không tìm thấy file chương-trước cho $(basename "$f") — chạy như đầu chuỗi"
    fi
  fi

  # Build the skill invocation against the LOCAL input copy.
  cmd="/visual-prompt:visual-prompt '$local_in' --series '$SERIES' --music $MUSIC"
  [ -n "$STYLE" ] && cmd="$cmd --style $STYLE"
  if [ "${VP_NO_VIDEO:-0}" = "1" ]; then
    cmd="$cmd --no-video"
    no_video_label=" (no-video)"
  else
    no_video_label=""
  fi
  if [ -n "$STYLE" ]; then
    style_label=" (style: $STYLE)"
  else
    style_label=""
  fi

  echo "▶ $tag — đang chạy${style_label}${no_video_label}"

  if [ "$DRYRUN" = "1" ]; then
    echo "   DRYRUN: (cd \"$SKILL_DIR\" && agy -p \"$cmd\" --model \"$MODEL\" --print-timeout 4h --dangerously-skip-permissions --add-dir \"$SKILL_DIR\" --add-dir \"$local_dir\" $BIBLES_ADD)"
    # simulate style-lock on the first file so dry-run shows later files inheriting it
    [ -z "$STYLE" ] && { STYLE="donghua-xianxia"; echo "   DRYRUN: (giả lập) khoá style=$STYLE → $CONF"; }
    continue
  fi

  # Run the skill + EXTERNAL bypass/depth gate, with a bounded --force-redo retry.
  # run-folder.sh is a thin driver the model cannot bypass: if the model shortcuts
  # via a self-made Python prompt generator (contract #4/#5/#6) or ships shallow /
  # boilerplate output, the gate rejects it and re-runs the file with --force-redo.
  # Up to 3 attempts; on persistent bypass the run is rejected (no garbage shipped).
  redo_ok=0
  for attempt in 1 2 3; do
    run_cmd="$cmd"
    if [ "$attempt" -gt 1 ]; then
      run_cmd="$cmd --force-redo"
      echo "   ⚠ $tag — re-run lần $attempt với --force-redo (lần trước bypass/shallow)"
    fi
    # Clear any self-made .py generators left by a prior bypass attempt.
    # --force-redo only removes scene-*.md / qa-* / music-*, NOT .py, so without
    # this the gate would re-flag the previous attempt's bypass .py even on a
    # clean LLM attempt (stale-poisoning the retry loop).
    rm -f "$local_dir"/.work/*.py 2>/dev/null
    # Also quarantine rogue code the model may have dropped in the SKILL ROOT
    # (= its CWD during a run) or hidden inside scripts/ under helper-looking
    # names (generate_plan.py, expand_scenes.py, fix_*.py) — a later run can
    # mistake those for canonical pipeline scripts and re-run the bypass. The
    # purge moves everything non-canonical into .quarantine-auto/ (recoverable),
    # so a clean retry never gets stale-poisoned by a prior attempt's bypass.
    python3 "$SKILL_DIR/scripts/check_run_legit.py" --purge-skill-dir "$SKILL_DIR" || true
    # NOTE: no `| tee <tmpfile>` — a pipe here can hang run-folder.sh. When agy
    # exits (e.g. on its internal "timed out waiting for response"), a lingering
    # child that inherited the pipe's write-end keeps tee's stdin open, so tee
    # never reads EOF and the pipeline never completes (run-folder.sh stalls
    # before the gate, even though the outputs are already written). agy's
    # stdout/stderr already flow to ~/vp-batch.log via the nohup redirect, so a
    # temp log is unnecessary. Direct redirect here — no pipe, no hang.
    ( cd "$SKILL_DIR" && agy -p "$run_cmd" \
        --model "$MODEL" \
        --print-timeout 4h \
        --dangerously-skip-permissions \
        --add-dir "$SKILL_DIR" \
        --add-dir "$local_dir" \
        $BIBLES_ADD ) 2>&1

    # First file just established the style — capture it and lock for the series.
    # Read from .work/active-style.md (deterministic first line "### <id> — ...").
    if [ -z "$STYLE" ]; then
      picked=$(sed -n 's/^### \([a-z0-9-][a-z0-9-]*\).*/\1/p' "$local_dir/.work/active-style.md" 2>/dev/null | head -1)
      if [ -n "$picked" ]; then
        STYLE="$picked"
        conf_set "$CONF" style "$STYLE"
        echo "🔒 $tag — khoá style cho bộ: $STYLE → $CONF"
      else
        echo "⚠ $tag — không bắt được 'Style:' từ output; file sau sẽ tự detect lại" >&2
      fi
    fi

    # Core artifact must exist before gating.
    if [ ! -s "${local_stem}_image_prompts.txt" ]; then
      [ "$attempt" -lt 3 ] && { echo "   ⚠ $tag — thiếu output, re-run"; continue; }
      die "$tag — thiếu/rỗng ${local_stem}_image_prompts.txt sau $attempt lần (chạy lại để resume)."
    fi

    # External gate: rejects .work/*.py prompt generators + shallow/boilerplate
    # outputs (the model cannot bypass this). Pass ⇒ legit deep LLM-expanded output.
    if python3 "$SKILL_DIR/scripts/check_run_legit.py" \
        --work "$local_dir/.work" --image "${local_stem}_image_prompts.txt" \
        --video "${local_stem}_video_prompts.txt" --skill-dir "$SKILL_DIR"; then
      redo_ok=1
      break
    fi
    [ "$attempt" -lt 3 ] && { echo "   ⚠ $tag — gate FAIL (bypass/shallow), re-run --force-redo"; continue; }
    die "$tag — gate vẫn FAIL sau 3 lần (model bypass expander). Output bị từ chối — chạy lại để resume."
  done
  [ "$redo_ok" = "1" ] || die "$tag — run không hợp lệ"
  bible_file="$HOME/.gemini/bibles/$SERIES.md"
  for kind in image video; do
    pf="${local_stem}_${kind}_prompts.txt"
    [ -s "$pf" ] || continue
    [ -f "$bible_file" ] && python3 "$SKILL_DIR/scripts/check_anchor_consistency.py" \
      --bible "$bible_file" --output "$pf" --fix
    # Content-safety gate: strip brand/IP/likeness/gore/sexual + ban live-action
    # video; religion is WARN-only. WARN does not halt the batch.
    python3 "$SKILL_DIR/scripts/check_content_safety.py" \
      --blocklist "$SKILL_DIR/references/blocklist-content-safety.md" \
      --output "$pf" --fix || true
  done

  # Copy the gated outputs back to the gdrive folder (only the final _*.txt; .work
  # scratch stays local). image is required (verified above); the rest are optional.
  cp "${local_stem}_image_prompts.txt" "${stem}_image_prompts.txt" \
    || die "$tag — không copy được _image_prompts.txt về $FOLDER"
  for suf in _qa.txt _video_prompts.txt _music_prompts.txt; do
    [ -s "${local_stem}${suf}" ] && cp "${local_stem}${suf}" "${stem}${suf}"
  done
  rm -rf "$local_dir"   # local scratch no longer needed; gdrive has the outputs
  echo "✅ $tag — xong (chạy local, đã copy output về gdrive)"
done

echo "✔ Hoàn tất bộ: $SERIES"
