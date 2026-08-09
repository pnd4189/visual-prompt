#!/usr/bin/env bash
#
# run-folder.sh — batch-drive the single-file /visual-prompt skill across one
# novel series folder, one chapter file at a time, each in a FRESH agy session.
#
# This is a THIN driver: it only orchestrates I/O and re-invokes the active Agy
# model. It NEVER generates prompts itself and NEVER calls an external
# model — every file is expanded by the real /visual-prompt pipeline. (RULE 0)
#
# Per series, the art style is detected once on the first file (skill scans the
# first chapters and picks #1), locked into <folder>/.vp-series.conf, then reused
# via --style for every later file so the whole series stays visually consistent
# and the interactive style prompt never reappears.
#
# Usage:   run-folder.sh <series-folder>
# Env:     VP_MODEL    pinned agy model        (default: "Gemini 3.1 Pro (High)")
#          VP_MUSIC    music loops per file     (default: 4)
#          VP_NO_VIDEO =1 → skip video prompts (default 0)
#          VP_NO_MUSIC =1 → skip music prompts (default 0; batch mode otherwise
#                      opts into music — direct /visual-prompt stays image-only)
#          VP_GLOB     input filename glob      (default '*.txt', e.g. '*_vi.txt')
#          VP_DRYRUN   =1 → print the agy command instead of running it (review)
#          VP_LOCAL    local workdir base       (default: $HOME/.cache/vp-run-<series>)
#          VP_WORKERS  opt-in bounded-parallel Pass-2 workers (default 1 = serial;
#                      >=2 = fan out after STEP 5, capped by remaining scene rows)
#
# Local-run strategy: the skill creates .work and writes its outputs next to the
# INPUT file. Running directly on a gdrive/rclone FUSE mount breaks parent-model writes
# (permission timeouts) and stalls on I/O, which pushes the model into bypassing the
# pipeline (external CLI calls, template fallback). So each file is copied to a fresh
# LOCAL dir, the whole pipeline runs there, and only the final _*.txt outputs are
# copied back to the gdrive folder.
#
# Resume:  file-level — only a file with a verified completion manifest is skipped.
#          Each file runs in a fresh local workdir, so a re-run after a crash
#          restarts the unfinished file while validated files stay skipped.

set -uo pipefail

MODEL="${VP_MODEL:-Gemini 3.1 Pro (High)}"
MUSIC="${VP_MUSIC:-4}"
DRYRUN="${VP_DRYRUN:-0}"
# Bounded-parallel Pass-2 workers (opt-in). 1/unset = serial, byte-for-byte the
# original path. >=2 = coordinator fans out isolated worker sessions after the
# scene plan exists (Phase 3); the count is capped by remaining scene rows.
WORKERS="${VP_WORKERS:-1}"

# Skill root = repo dir holding scripts/ + prompts/. Agy inherits the launch
# CWD; we run it from here so the skill's relative paths (scripts/load_input.py,
# @prompts/*.md) resolve. Otherwise the model can't find them and may launch a
# runaway `find /home -name ...` that traverses gdrive mounts for hours.
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

die() { echo "❌ $*" >&2; exit 1; }

completion_manifest() {
  python3 - "$@" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

mode, manifest_name, input_name, image_name, music_name, qa_name, video_name, \
    plan_name, skill_dir_name, series, style, model, music_n, no_video, no_music = sys.argv[1:]


def digest(filename):
    path = Path(filename)
    data = path.read_bytes()
    if not data:
        raise ValueError(f'empty completion artifact: {path}')
    return hashlib.sha256(data).hexdigest()


try:
    skill_dir = Path(skill_dir_name)
    skill_version = json.loads(
        (skill_dir / 'gemini-extension.json').read_text(encoding='utf-8')
    )['version']
    no_video_enabled = no_video == '1'
    no_music_enabled = no_music == '1'
    count = 0 if no_music_enabled else int(music_n)
    plan_path = Path(plan_name)
    artifacts = {
        'input': digest(input_name),
        'image': digest(image_name),
        'qa': digest(qa_name),
    }
    if not no_music_enabled:
        artifacts['music'] = digest(music_name)
        artifacts['music_plan'] = digest(plan_path)
        artifacts['music_regions'] = [
            digest(plan_path.parent / f'music-{index:03d}.md')
            for index in range(1, count + 1)
        ]
    if not no_video_enabled:
        artifacts['video'] = digest(video_name)
    expected = {
        'schema': 1,
        'skill_version': skill_version,
        'series': series,
        'style': style,
        'model': model,
        'music_n': count,
        'no_video': no_video_enabled,
        'artifacts': artifacts,
    }
    if no_music_enabled:
        # New key only when active: existing music-enabled manifests (no key)
        # must keep verifying byte-for-byte so resume is not invalidated.
        expected['no_music'] = True
    manifest = Path(manifest_name)
    if mode == 'verify':
        actual = json.loads(manifest.read_text(encoding='utf-8'))
        raise SystemExit(0 if actual == expected else 1)
    if mode != 'write':
        raise ValueError(f'unknown completion-manifest mode: {mode}')
    payload = json.dumps(expected, indent=2) + '\n'
    # Destination is commonly a gdrive FUSE mount where rename is unsupported.
    # A torn direct write fails exact JSON verification and therefore fails closed.
    manifest.write_text(payload, encoding='utf-8')
    if manifest.read_text(encoding='utf-8') != payload:
        raise OSError(f'completion manifest verification failed: {manifest}')
except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError):
    raise SystemExit(1)
PY
}

# agy_harness <run_cmd> <workdir> <batch_token> <mode> [worker_manifest] [extra_dir]
# mode: full | plan | worker. Serial runs call mode=full — behavior is identical
# to the original inline harness (approval markers, CLI-feedback skip, completion
# hints, nonce-scoped BATCH_RUN_COMPLETE/HALTED). plan/worker sessions only vary
# the "outputs ready" hint set, the deadline, and an extra read-only dir.
agy_harness() {
python3 - "$1" "$MODEL" "$SKILL_DIR" "$2" "$BIBLES_DIR" "$3" "${4:-full}" "${5:-}" "${6:-}" <<'PY'
import json
import os
import re
import sys
import time
from pathlib import Path

import pexpect

(run_cmd, model, skill_dir, local_dir, bibles_dir, batch_token, mode,
 worker_manifest, extra_dir) = sys.argv[1:10]
args = [
    '-i', run_cmd,
    '--model', model,
    '--agent', 'visual-prompt-writer',
    '--mode', 'accept-edits',
    '--sandbox',
    # accept-edits auto-approves file edits only: every run_command still raises
    # an interactive confirmation that nobody answers in an unattended batch, so
    # the first helper call hangs the whole attempt. Permission prompts are not
    # the safety layer here — the runtime guard denies non-canonical tools and
    # commands at PreToolUse, and it keeps doing so with prompts disabled.
    '--dangerously-skip-permissions',
    '--add-dir', skill_dir,
    '--add-dir', local_dir,
]
if os.path.isdir(bibles_dir):
    args.extend(['--add-dir', bibles_dir])
if extra_dir and os.path.isdir(extra_dir):
    args.extend(['--add-dir', extra_dir])

attempt_started = time.time()
local_path = Path(local_dir)
for resource in ('.agents', 'scripts', 'prompts', 'references'):
    link = local_path / resource
    source = Path(skill_dir) / resource
    if not link.exists():
        link.symlink_to(source, target_is_directory=True)
if mode == 'worker':
    authorship_log = str(Path(worker_manifest).with_suffix('.authorship.jsonl'))
    allowed_roots = [local_dir]
else:
    authorship_log = str(local_path / '.work' / 'active-model-authorship.jsonl')
    allowed_roots = [str(local_path / '.work')]
    if os.path.isdir(bibles_dir):
        allowed_roots.append(bibles_dir)
guard_env = os.environ.copy()
guard_env.update({
    'VP_GUARD_ACTIVE': '1',
    'VP_GUARD_STATE': str(Path(authorship_log).parent / f'.guard-{batch_token}.json'),
    'VP_AUTHORSHIP_LOG': authorship_log,
    'VP_ALLOWED_WRITE_ROOTS': os.pathsep.join(allowed_roots),
    'VP_ALLOWED_OUTPUT_ROOTS': local_dir,
    # Plan-only and worker sessions stop before assembly by design, so the
    # closing gate must not hold them; the coordinator runs it after the join.
    'VP_GUARD_STOP_GATE': '0' if mode in ('plan', 'worker') else '1',
})
child = pexpect.spawn(
    'agy', args, cwd=local_dir, env=guard_env,
    encoding='utf-8', codec_errors='replace',
    timeout=90,
)
child.delaybeforesend = 0.1
ansi = r'(?:\x1b\[[0-?]*[ -/]*[@-~])*'
line_start = r'(?m)(?:^|\r?\n)' + ansi + r'[ \t]*'
line_end = r'[ \t]*' + ansi + r'(?=\r?$)'
patterns = [
    re.compile(line_start + r'BATCH_APPROVAL_REQUIRED:' + re.escape(batch_token) + line_end),
    re.compile(
        r'(?:Bạn có đồng ý với kế hoạch(?: này| trên)?|Xin(?: bạn| vui lòng)? xác nhận kế hoạch(?: này| trên)?|Xác nhận để bắt đầu tiến hành)',
        re.IGNORECASE,
    ),
    re.compile(
        line_start + r"How's the CLI experience so far\? Help us improve:" + line_end,
        re.IGNORECASE,
    ),
    re.compile(line_start + r'BATCH_RUN_COMPLETE:' + re.escape(batch_token) + line_end),
    re.compile(line_start + r'BATCH_RUN_HALTED:' + re.escape(batch_token) + line_end),
    pexpect.EOF,
    pexpect.TIMEOUT,
]
approvals = 0
max_auto_approvals = 6
completion_nudges = 0
# A model that yields its turn early leaves the CLI idle at the prompt: no
# pattern ever matches and the attempt would burn its whole deadline in silence.
# Nudge a few times, then fail fast so the normal retry path takes over.
idle_rounds = 0
idle_nudges = 0
max_idle_nudges = 4


def artifact_pulse(root):
    """Newest mtime among the run's own files — symlinked skill dirs excluded."""
    latest = 0.0
    for folder in (root, root / '.work'):
        try:
            entries = list(folder.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_symlink() or entry.is_dir():
                continue
            try:
                latest = max(latest, entry.stat().st_mtime)
            except OSError:
                continue
    return latest


last_pulse = artifact_pulse(local_path)
deadline_seconds = {'full': 4 * 3600, 'plan': 3 * 3600, 'worker': 2 * 3600}[mode]
deadline = time.monotonic() + deadline_seconds
outcome = None


def scene_filename(scene_id):
    match = re.fullmatch(r'(\d+)([a-zA-Z]?)', str(scene_id))
    return f'scene-{int(match.group(1)):03d}{match.group(2)}.md'


try:
    while outcome is None:
        matched = child.expect(patterns)
        if matched in (0, 1):
            approvals += 1
            if approvals > max_auto_approvals:
                raise RuntimeError('Agy requested approval more than 6 times')
            print(
                f'   agy: plan received — auto-approved '
                f'({approvals}/{max_auto_approvals})',
                flush=True,
            )
            child.sendline(
                'Tôi xác nhận kế hoạch vừa nêu. Hãy thực thi ngay toàn bộ batch '
                'đã được phê duyệt, không hỏi lại.'
            )
        elif matched == 2:
            print('   agy: CLI feedback prompt — skipped', flush=True)
            child.sendline('0')
        elif matched == 3:
            print('   agy: reported workflow complete', flush=True)
            outcome = 0
        elif matched == 4:
            print('   agy: reported workflow halted', flush=True)
            outcome = 2
        elif matched == 5:
            tail = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', child.before or '')[-800:]
            print(f'   agy: exited before batch marker: {tail}', file=sys.stderr)
            outcome = 1
        else:
            if time.monotonic() >= deadline:
                raise TimeoutError('Agy interactive run exceeded its deadline')
            local_stem = local_path / local_path.name
            if mode == 'plan':
                expected_outputs = [
                    local_path / '.work' / 'scene-plan.md',
                    local_path / '.work' / 'chapters_qa.json',
                ]
                ready_label = 'scene plan ready'
            elif mode == 'worker':
                payload = json.loads(Path(worker_manifest).read_text(encoding='utf-8'))
                worker_path = Path(payload['work_dir'])
                expected_outputs = [
                    worker_path / scene_filename(scene_id)
                    for scene_id in payload['scene_ids']
                ]
                ready_label = 'assigned scenes ready'
            else:
                expected_outputs = [
                    Path(f'{local_stem}_qa.txt'),
                    Path(f'{local_stem}_image_prompts.txt'),
                    local_path / '.work' / 'scene-plan.md',
                ]
                if os.environ.get('VP_NO_MUSIC') != '1':
                    expected_outputs.append(Path(f'{local_stem}_music_prompts.txt'))
                ready_label = 'assembled outputs found'
            outputs_ready = all(
                path.is_file() and path.stat().st_size > 0
                and path.stat().st_mtime >= attempt_started
                for path in expected_outputs
            )
            completion_hint = local_path / '.vp-completion.json'
            if not completion_hint.is_file():
                completion_hint = local_path / '.vp-complete.json'
            post_gate_hint = local_path / '.work' / 'completion_manifest.json'
            if mode == 'full' and post_gate_hint.is_file():
                print('   agy: post-gate manifest found — continuing to external gates', flush=True)
                outcome = 0
                continue
            ready = outputs_ready
            if mode == 'full':
                ready = ready or completion_hint.is_file()
            if not ready:
                # Liveness must come from artifacts, not from the stream: an idle
                # Agy TUI keeps redrawing, so "no bytes received" never happens.
                pulse = artifact_pulse(local_path)
                if pulse > last_pulse:
                    last_pulse, idle_rounds = pulse, 0
                else:
                    idle_rounds += 1
                # Two silent rounds (~3 min) — Agy models routinely yield their
                # turn after a denied tool call and then wait for a human.
                if idle_rounds >= 2:
                    idle_nudges += 1
                    if idle_nudges > max_idle_nudges:
                        raise RuntimeError(
                            'Agy stalled: no output and no artifacts after '
                            f'{max_idle_nudges} nudges'
                        )
                    idle_rounds = 0
                    print(
                        f'   agy: idle — nudging ({idle_nudges}/{max_idle_nudges})',
                        flush=True,
                    )
                    child.sendline(
                        'Phiên vẫn đang chạy pipeline visual-prompt. Tiếp tục STEP '
                        'đang dở ngay bây giờ, tự viết từng scene, không hỏi lại.'
                    )
                continue
            if ready and completion_nudges >= 3:
                # Every expected artifact is present and fresh; the model just
                # will not emit the marker. Accept the artifacts and let the
                # driver's own gate battery decide — waiting longer only burns
                # the deadline.
                print('   agy: outputs complete, no marker — accepting artifacts',
                      flush=True)
                outcome = 0
                continue
            if ready:
                completion_nudges += 1
                print(
                    f'   agy: {ready_label} — requesting final marker '
                    f'({completion_nudges}/3)',
                    flush=True,
                )
                child.sendline(
                    'Nếu workflow đã hoàn tất, hãy trả marker kết thúc nonce-scoped '
                    'đã được yêu cầu trong instruction. Nếu chưa, hoàn tất gate trước.'
                )
finally:
    if child.isalive():
        child.sendcontrol('d')
        try:
            child.expect(pexpect.EOF, timeout=10)
        except (pexpect.TIMEOUT, pexpect.EOF):
            child.close(force=True)

raise SystemExit(outcome)
PY
}

[[ "$MUSIC" =~ ^[1-9][0-9]*$ ]] || die "VP_MUSIC phải là số nguyên >= 1: $MUSIC"
[[ "$WORKERS" =~ ^[1-9][0-9]*$ ]] || die "VP_WORKERS phải là số nguyên >= 1: $WORKERS"
[ "$WORKERS" -le 16 ] || die "VP_WORKERS tối đa 16 (hiện là $WORKERS) — tăng worker không được nới gate."
case "${VP_NO_VIDEO:-0}" in 0|1) ;; *) die "VP_NO_VIDEO phải là 0 hoặc 1" ;; esac
case "${VP_NO_MUSIC:-0}" in 0|1) ;; *) die "VP_NO_MUSIC phải là 0 hoặc 1" ;; esac
INPUT_GLOB="${VP_GLOB:-*.txt}"
[ -n "$INPUT_GLOB" ] || die "VP_GLOB không được rỗng"

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
SAFE_SERIES=$(slugify "$SERIES")
[ -n "$SAFE_SERIES" ] || die "Series name không tạo được filesystem-safe slug: $SERIES"
[ "$SAFE_SERIES" = "$SERIES" ] \
  || echo "⚠ Chuẩn hoá series '$SERIES' → '$SAFE_SERIES' để bảo vệ đường dẫn." >&2
SERIES="$SAFE_SERIES"
conf_set "$CONF" series "$SERIES"

# Pre-flight: refuse to run if the pinned model name no longer exists in agy.
# Fails loud (instead of silently using a wrong/weaker default) when Google
# renames or retires a model — change VP_MODEL and re-run.
if [ "$DRYRUN" != "1" ]; then
  python3 -c 'import pexpect' 2>/dev/null \
    || die "Thiếu Python package pexpect để điều khiển Agy interactive."
  available_models=$(agy models 2>/dev/null) || die "Không đọc được danh sách model từ agy."
  grep -qF "$MODEL" <<< "$available_models" || {
    echo "❌ Model '$MODEL' không còn trong agy. Danh sách hiện có:" >&2
    printf '%s\n' "$available_models" >&2
    die "Sửa VP_MODEL rồi chạy lại (vd: VP_MODEL='Gemini 4 Pro (High)' $0 '$FOLDER')."
  }
  available_agents=$(agy agent 2>/dev/null) || die "Không đọc được danh sách agent từ agy."
  grep -qxF "visual-prompt-writer" <<< "$available_agents" \
    || die "Agy chưa nạp primary agent visual-prompt-writer. Chạy bash setup.sh rồi mở phiên Agy mới."
fi

# Load a previously locked style for this series from the shared config, if any.
STYLE=$(conf_get "$CONF" style)

# Base dir for per-file local workdirs (keeps the pipeline off the gdrive FUSE
# mount). Default under $HOME/.cache, NOT /tmp — /tmp is cleared on reboot, and
# an overnight reboot wiped a 6-file batch's local workdirs mid-run. A persistent
# base survives reboot; each file still gets a fresh subdir (rm -rf per file).
LOCAL_BASE="${VP_LOCAL:-$HOME/.cache/vp-run-$SERIES}"

# Grant agy read access to the series bibles dir so the active parent model can
# read ~/.gemini/bibles/<series>.md directly. Without this, the bible path is
# outside --add-dir, the model may fabricate generic appearance, and
# restart expansion mid-run to fix it — that restart can make the model yield
# before assemble, so no output ships. The interactive controller adds this
# directory only when it exists.
BIBLES_DIR="$HOME/.gemini/bibles"

# Collect input chapter files in chapter order (filenames sort lexically:
# _0001_0010, _0011_0020, ...). Output .txt files are excluded. VP_GLOB selects
# the input pattern (default '*.txt'; e.g. '*_vi.txt' to run only translations
# when raw + _vi copies coexist in one folder).
mapfile -t FILES < <(find "$FOLDER" -maxdepth 1 -type f -name "$INPUT_GLOB" | sort)
INPUTS=()
for f in "${FILES[@]}"; do is_output_file "$f" || INPUTS+=("$f"); done
[ ${#INPUTS[@]} -gt 0 ] || die "Không có file truyện .txt nào khớp '$INPUT_GLOB' trong: $FOLDER"

music_label="$MUSIC"
[ "${VP_NO_MUSIC:-0}" = "1" ] && music_label="off"
echo "▶ Bộ: $SERIES | model: $MODEL | music: $music_label | video: $([ "${VP_NO_VIDEO:-0}" = "1" ] && echo off || echo on) | glob: $INPUT_GLOB | files: ${#INPUTS[@]} | style: ${STYLE:-(auto file đầu)}"

total=${#INPUTS[@]}; idx=0
for f in "${INPUTS[@]}"; do
  idx=$((idx + 1))
  stem="${f%.txt}"
  tag="[$SERIES] $idx/$total $(basename "$f")"
  music_cache="${stem}_music-cache"
  complete_manifest="${stem}_visual-prompt-complete.json"
  video_output="${stem}_video_prompts.txt"

  if completion_manifest verify "$complete_manifest" "$f" \
      "${stem}_image_prompts.txt" "${stem}_music_prompts.txt" "${stem}_qa.txt" \
      "$video_output" "$music_cache/music-plan.md" "$SKILL_DIR" "$SERIES" \
      "$STYLE" "$MODEL" "$MUSIC" "${VP_NO_VIDEO:-0}" "${VP_NO_MUSIC:-0}"; then
    echo "⏭  $tag — đã có output, skip"
    continue
  fi

  # Run on LOCAL disk, not gdrive. The skill creates .work + writes its outputs next
  # to the INPUT file; copying the input into a fresh local dir keeps all that churn
  # off the gdrive FUSE mount (which breaks parent-model writes and stalls on I/O). Fresh
  # dir per file → no cross-file scratch leakage. Pre-create .work so the pipeline's
  # `> .work/chapters.json` (STEP 1) has its dir. Outputs get copied back after.
  local_dir="$LOCAL_BASE/$(basename "$stem")"
  local_in="$local_dir/$(basename "$f")"
  local_stem="${local_in%.txt}"
  if [ "$DRYRUN" = "1" ]; then
    echo "   DRYRUN: reset \"$local_dir/.work\"; restore music cache nếu có; chạy local; copy outputs + music cache về \"$FOLDER\""
  else
    rm -rf "$local_dir" && mkdir -p "$local_dir/.work"
    cp "$f" "$local_in" || die "$tag — không copy được input sang local dir $local_dir"
    if [ "${VP_NO_MUSIC:-0}" != "1" ] && [ -s "$music_cache/music-plan.md" ]; then
      cp "$music_cache/music-plan.md" "$local_dir/.work/music-plan.md" \
        || die "$tag — không restore được music-plan cache"
      cached_music_n=$(sed -n 's/^music_n:[[:space:]]*//p' "$music_cache/music-plan.md" | head -1)
      if [[ "$cached_music_n" =~ ^[0-9]+$ ]]; then
        cache_index=1
        while [ "$cache_index" -le "$cached_music_n" ]; do
          printf -v cache_name 'music-%03d.md' "$cache_index"
          [ -s "$music_cache/$cache_name" ] \
            && cp "$music_cache/$cache_name" "$local_dir/.work/$cache_name"
          cache_index=$((cache_index + 1))
        done
      fi
    fi
    # Pre-stage the skill's prompts/ + references/ into the local workdir so the
    # active model resolves `@prompts/*.md` / `@references/*.md`
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

  # Batch mode explicitly opts into music and video unless VP_NO_MUSIC /
  # VP_NO_VIDEO disable them; direct /visual-prompt runs remain image-only by
  # default.
  # Every folder run is explicitly pre-approved and unattended. Without this flag,
  # Agy may stop after presenting a plan and never write outputs.
  cmd="/visual-prompt:visual-prompt '$local_in' --series '$SERIES' --auto-repair"
  if [ "${VP_NO_MUSIC:-0}" = "1" ]; then
    cmd="$cmd --no-music"
  else
    cmd="$cmd --music $MUSIC"
  fi
  [ -n "$STYLE" ] && cmd="$cmd --style $STYLE"
  if [ "${VP_NO_VIDEO:-0}" = "1" ]; then
    cmd="$cmd --no-video"
    no_video_label=" (no-video)"
  else
    cmd="$cmd --video"
    no_video_label=""
  fi
  if [ "${VP_NO_MUSIC:-0}" = "1" ]; then
    no_music_label=" (no-music)"
  else
    no_music_label=""
  fi
  if [ -n "$STYLE" ]; then
    style_label=" (style: $STYLE)"
  else
    style_label=""
  fi

  echo "▶ $tag — đang chạy${style_label}${no_video_label}${no_music_label}"

  if [ "$DRYRUN" = "1" ]; then
    echo "   DRYRUN: Agy interactive controller → plan approval → execution (model=$MODEL, mode=accept-edits, timeout=4h)"
    echo "   DRYRUN: gate order legit → artifacts → similarity → anchor/safety --fix → final artifacts/similarity → copy/cache → history/manifest"
    if [ "$WORKERS" -ge 2 ]; then
      echo "   DRYRUN: parallel pass-2: VP_WORKERS=$WORKERS (head --plan-only → worker fan-out --worker-manifest → tail full; mọi gate post-join giữ nguyên)"
    fi
    # simulate style-lock on the first file so dry-run shows later files inheriting it
    [ -z "$STYLE" ] && { STYLE="donghua-xianxia"; echo "   DRYRUN: (giả lập) khoá style=$STYLE → $CONF"; }
    continue
  fi

  # Run the skill + EXTERNAL bypass/depth gate. Full generation is bounded to
  # three attempts, while a failed similarity/boilerplate gate may request up
  # to ten small, validated repair batches. This avoids asking one Agy turn to
  # rewrite an entire 120-scene output while keeping every external gate.
  # run-folder.sh is a thin driver the model cannot bypass: if the model shortcuts
  # via a self-made runtime prompt generator (contract #4/#5/#6) or ships shallow /
  # boilerplate output, the gate rejects it and re-runs the file with --force-redo.
  # A persistent bypass is rejected; nothing ships before every gate passes.
  redo_ok=0
  force_redo_next=0
  max_full_attempts=3
  max_targeted_repairs=10
  repair_chunk_size="${VP_REPAIR_CHUNK_SIZE:-12}"
  if ! [[ "$repair_chunk_size" =~ ^[1-9][0-9]*$ ]] || [ "$repair_chunk_size" -gt 24 ]; then
    die "VP_REPAIR_CHUNK_SIZE phải là số từ 1 đến 24 (hiện là '$repair_chunk_size')."
  fi
  full_attempts=0
  targeted_repairs=0
  attempt=0
  driver_state=$(mktemp -d "$LOCAL_BASE/.driver-state.XXXXXX") \
    || die "$tag — không tạo được private driver state."
  chmod 700 "$driver_state" || die "$tag — không khoá được private driver state."
  similarity_feedback="$driver_state/similarity-feedback.md"
  legit_report="$driver_state/legit-report.json"
  last_repair_signature=''

  # ---- Bounded-parallel Pass-2 (opt-in: VP_WORKERS >= 2) -------------------
  # Head session (--plan-only) runs STEP 1-5.5 and freezes QA/bible/style/plan
  # into a read-only snapshot; worker sessions expand disjoint scene ranges in
  # isolated workdirs; the join verifies ownership + full coverage BEFORE any
  # shared-state write. The while-loop below then acts as the tail: its
  # full-mode session skips cached scenes (STEP 6 resume), runs music/assemble/
  # gates, and every post-join gate stays coordinator-only. Any head/fan-out/
  # join failure falls through to unchanged serial full generation in the loop.
  parallel_ok=0
  workers_base="$LOCAL_BASE/.workers/$(basename "${local_in%.txt}")"
  if [ "$WORKERS" -ge 2 ]; then
    fanout_started=$SECONDS
    echo "▶ $tag — parallel pass-2: VP_WORKERS=$WORKERS (head --plan-only → workers → tail)"
    head_token=$(python3 -c 'import secrets; print(secrets.token_hex(12))') \
      || die "$tag — không tạo được head batch token."
    rm -f "$local_dir/.vp-completed.json" "$local_dir/.vp-completion.json" \
      "$local_dir/.work/completion_manifest.json" 2>/dev/null
    python3 "$SKILL_DIR/scripts/check_run_legit.py" --purge-skill-dir "$SKILL_DIR" || true
    agy_harness "$cmd --plan-only --batch-token '$head_token'" \
      "$local_dir" "$head_token" plan > "$driver_state/head-session.log" 2>&1
    head_status=$?
    plan_gate_ok=0
    if [ "$head_status" -eq 0 ] && [ -s "$local_dir/.work/scene-plan.md" ] \
        && [ -s "$local_dir/.work/chapters_qa.json" ]; then
      if python3 "$SKILL_DIR/scripts/validate_scene_plan.py" \
          --plan "$local_dir/.work/scene-plan.md" \
          --chapters-json "$local_dir/.work/chapters_qa.json" \
          > "$driver_state/head-plan-gate.json"; then
        plan_gate_ok=1
      fi
    fi
    worker_manifests=()
    if [ "$plan_gate_ok" = "1" ]; then
      video_enabled_flag=0
      [ "${VP_NO_VIDEO:-0}" != "1" ] && video_enabled_flag=1
      # Freeze the snapshot + split disjoint ranges + write immutable manifests.
      mapfile -t worker_manifests < <(python3 - "$SKILL_DIR/scripts" "$local_dir" \
          "$driver_state" "$WORKERS" "$HOME/.gemini/bibles/$SERIES.md" \
          "$HOME/.gemini/bibles/$SERIES-visual-history.md" "$workers_base" \
          "$video_enabled_flag" <<'PY'
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])
import worker_manifest as wm

(local_dir, driver_state, workers_cap, bible_path,
 history_path, workers_base, video_flag) = sys.argv[2:9]
work = Path(local_dir) / '.work'
snapshot = Path(driver_state) / 'snapshot'
snapshot.mkdir(parents=True, exist_ok=True)
bundle = {
    'qa_hash': (work / 'chapters_qa.json', 'chapters_qa.json'),
    'plan_hash': (work / 'scene-plan.md', 'scene-plan.md'),
    'style_hash': (work / 'active-style.md', 'active-style.md'),
    'bible_hash': (Path(bible_path), 'character-bible.md'),
}
hashes = {}
for field, (source, dest) in bundle.items():
    if not source.is_file() or source.stat().st_size == 0:
        print(f'freeze FAIL: thiếu {source}', file=sys.stderr)
        raise SystemExit(2)
    shutil.copy2(source, snapshot / dest)
    hashes[field] = hashlib.sha256((snapshot / dest).read_bytes()).hexdigest()
history_hash = ''
history_source = Path(history_path)
if history_source.is_file() and history_source.stat().st_size > 0:
    shutil.copy2(history_source, snapshot / 'visual-history.md')
    history_hash = hashlib.sha256(
        (snapshot / 'visual-history.md').read_bytes()
    ).hexdigest()
ranges, violations = wm.split_plan(work / 'scene-plan.md', int(workers_cap))
if violations:
    print('freeze FAIL: ' + '; '.join(violations), file=sys.stderr)
    raise SystemExit(2)
base = Path(workers_base)
for entry in ranges:
    worker_dir = base / entry['worker_id']
    worker_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        'schema': 1,
        'worker_id': entry['worker_id'],
        'scene_ids': entry['scene_ids'],
        **hashes,
        'history_hash': history_hash,
        'snapshot_dir': str(snapshot),
        'work_dir': str(worker_dir),
        'video_enabled': video_flag == '1',
    }
    path = Path(driver_state) / f"manifest-{entry['worker_id']}.json"
    path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(path)
PY
      )
      [ ${#worker_manifests[@]} -gt 0 ] \
        || echo "   ⚠ $tag — freeze snapshot FAIL, fallback serial (log: $driver_state)"
    else
      echo "   ⚠ $tag — head --plan-only FAIL (exit $head_status, log: $driver_state/head-session.log), fallback serial"
    fi

    join_ok=0
    if [ ${#worker_manifests[@]} -gt 0 ]; then
      # Fan out: one isolated agy session per manifest (own workdir, token,
      # direct-redirect log — no tee), all sharing the read-only snapshot.
      worker_pids=()
      for m in "${worker_manifests[@]}"; do
        wtoken=$(python3 -c 'import secrets; print(secrets.token_hex(12))') \
          || die "$tag — không tạo được worker batch token."
        wdir=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['work_dir'])" "$m")
        agy_harness "$cmd --worker-manifest '$m' --batch-token '$wtoken'" \
          "$wdir" "$wtoken" worker "$m" "$driver_state/snapshot" \
          > "$driver_state/$(basename "$m" .json).log" 2>&1 &
        worker_pids+=("$!")
      done
      worker_exits=()
      for pid in "${worker_pids[@]}"; do
        wait "$pid"
        worker_exits+=("$?")
      done
      # Join: ownership fence + worker-run legit gate per worker. A failed
      # range gets ONE bounded retry — same immutable manifest (STEP 6 cache
      # resume makes the respawn idempotent), fresh token.
      join_ok=1
      retry_manifests=()
      for i in "${!worker_manifests[@]}"; do
        m="${worker_manifests[$i]}"
        wlog="$driver_state/$(basename "$m" .json)"
        wdir=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['work_dir'])" "$m")
        if [ "${worker_exits[$i]}" -ne 0 ]; then
          echo "   ⚠ $tag — worker $(basename "$m" .json) exit ${worker_exits[$i]} (log: $wlog.log)"
        fi
        if python3 "$SKILL_DIR/scripts/worker_manifest.py" --verify-run "$m" > "$wlog.verify.json" \
            && python3 "$SKILL_DIR/scripts/check_run_legit.py" \
              --work "$wdir" --worker-manifest "$m" --require-authorship \
              --authorship-log "${m%.json}.authorship.jsonl" > "$wlog.legit.txt"; then
          continue
        fi
        join_ok=0
        retry_manifests+=("$m")
      done
      if [ "$join_ok" != "1" ] && [ ${#retry_manifests[@]} -gt 0 ]; then
        echo "   ⚠ $tag — bounded targeted retry: ${#retry_manifests[@]} worker range(s)"
        retry_pids=()
        for m in "${retry_manifests[@]}"; do
          wtoken=$(python3 -c 'import secrets; print(secrets.token_hex(12))') \
            || die "$tag — không tạo được retry worker batch token."
          wdir=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['work_dir'])" "$m")
          agy_harness "$cmd --worker-manifest '$m' --batch-token '$wtoken'" \
            "$wdir" "$wtoken" worker "$m" "$driver_state/snapshot" \
            > "$driver_state/$(basename "$m" .json)-retry.log" 2>&1 &
          retry_pids+=("$!")
        done
        join_ok=1
        for i in "${!retry_manifests[@]}"; do
          m="${retry_manifests[$i]}"
          wait "${retry_pids[$i]}"
          wexit=$?
          wlog="$driver_state/$(basename "$m" .json)"
          wdir=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['work_dir'])" "$m")
          if [ "$wexit" -ne 0 ] \
              || ! python3 "$SKILL_DIR/scripts/worker_manifest.py" --verify-run "$m" > "$wlog.verify-retry.json" \
              || ! python3 "$SKILL_DIR/scripts/check_run_legit.py" \
                    --work "$wdir" --worker-manifest "$m" --require-authorship \
                    --authorship-log "${m%.json}.authorship.jsonl" > "$wlog.legit-retry.txt"; then
            join_ok=0
            echo "   ⚠ $tag — retry worker $(basename "$m" .json) vẫn FAIL"
          fi
        done
      fi
    fi

    if [ "$join_ok" = "1" ] && [ ${#worker_manifests[@]} -gt 0 ]; then
      merge_ok=1
      authorship_log="$local_dir/.work/active-model-authorship.jsonl"
      for m in "${worker_manifests[@]}"; do
        wdir=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['work_dir'])" "$m")
        cp "$wdir"/scene-*.md "$local_dir/.work/" 2>/dev/null || merge_ok=0
        worker_authorship="${m%.json}.authorship.jsonl"
        [ -s "$worker_authorship" ] && cat "$worker_authorship" >> "$authorship_log" \
          || merge_ok=0
      done
      if [ "$merge_ok" = "1" ] && python3 - "$SKILL_DIR/scripts" \
          "$local_dir/.work/scene-plan.md" "$local_dir/.work" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from validate_artifacts import _scene_filename, _scene_plan_details
scene_ids, _, plan_errors, _, _ = _scene_plan_details(Path(sys.argv[2]))
if plan_errors:
    raise SystemExit(2)
work = Path(sys.argv[3])
missing = [sid for sid in scene_ids if not (work / _scene_filename(sid)).is_file()]
if missing:
    print(f'worker join thiếu {len(missing)} scene: {missing[:10]}', file=sys.stderr)
    raise SystemExit(2)
PY
      then
        parallel_ok=1
        echo "✔ $tag — parallel pass-2 join OK: ${#worker_manifests[@]} workers, $((SECONDS - fanout_started))s (tail session chạy music/assemble/gates)"
      else
        echo "   ⚠ $tag — worker join: thiếu coverage sau merge, fallback serial"
      fi
    fi
    [ "$parallel_ok" = "1" ] \
      || echo "   ⚠ $tag — parallel pass-2 không hoàn tất; vòng lặp serial full-generate (scene hợp lệ đã có được cache-skip tái sử dụng)"
  fi

  schedule_force_redo() {
    if [ "$full_attempts" -lt "$max_full_attempts" ]; then
      force_redo_next=1
      last_repair_signature=''
      return 0
    fi
    return 1
  }
  schedule_targeted_repair() {
    local signature="$1"
    if [ "$signature" = "$last_repair_signature" ]; then
      return 2
    fi
    if [ "$targeted_repairs" -lt "$max_targeted_repairs" ]; then
      force_redo_next=0
      last_repair_signature="$signature"
      return 0
    fi
    return 1
  }
  while :; do
    attempt=$((attempt + 1))
    run_cmd="$cmd"
    if [ "$force_redo_next" = "1" ]; then
      full_attempts=$((full_attempts + 1))
      run_cmd="$cmd --force-redo"
      rm -f "$local_dir"/.work/music-*.md "${local_stem}_music_prompts.txt"
      echo "   ⚠ $tag — full retry $full_attempts/$max_full_attempts (run $attempt, --force-redo)"
    elif [ -s "$similarity_feedback" ]; then
      targeted_repairs=$((targeted_repairs + 1))
      run_cmd="$cmd --similarity-feedback '$similarity_feedback'"
      echo "   ⚠ $tag — targeted repair $targeted_repairs/$max_targeted_repairs (tối đa $repair_chunk_size IDs)"
    else
      full_attempts=$((full_attempts + 1))
      echo "   ℹ $tag — full generation $full_attempts/$max_full_attempts (run $attempt)"
    fi
    batch_token=$(python3 -c 'import secrets; print(secrets.token_hex(12))') \
      || die "$tag — không tạo được batch approval token."
    run_cmd="$run_cmd --batch-token '$batch_token'"
    # Clear any self-made .py generators left by a prior bypass attempt.
    # --force-redo only removes scene-*.md / qa-* / music-*, NOT .py, so without
    # this the gate would re-flag the previous attempt's bypass .py even on a
    # clean LLM attempt (stale-poisoning the retry loop).
    rm -f "$local_dir"/.work/*.py "$local_dir/.vp-completed.json" \
      "$local_dir/.vp-completion.json" \
      "$local_dir/.work/completion_manifest.json" 2>/dev/null
    # Also quarantine rogue code the model may have dropped in the SKILL ROOT
    # (= its CWD during a run) or hidden inside scripts/ under helper-looking
    # names (generate_plan.py, expand_scenes.py, fix_*.py) — a later run can
    # mistake those for canonical pipeline scripts and re-run the bypass. The
    # purge moves everything non-canonical into .quarantine-auto/ (recoverable),
    # so a clean retry never gets stale-poisoned by a prior attempt's bypass.
    python3 "$SKILL_DIR/scripts/check_run_legit.py" --purge-skill-dir "$SKILL_DIR" || true
    # Agy's global workflow requires plan acknowledgement for large edits. Print
    # mode cannot receive that second turn, so agy_harness drives one interactive
    # conversation: wait for the explicit approval marker, send the operator's
    # approval, then wait for a completion/halt marker. The external gates below
    # remain authoritative. mode=full keeps serial behavior unchanged.
    agy_harness "$run_cmd" "$local_dir" "$batch_token" full
    agy_status=$?
    if [ "$agy_status" -eq 2 ]; then
      die "$tag — Agy báo HALT; giữ local artifacts tại $local_dir, không auto-retry/force-redo."
    fi
    if [ "$agy_status" -ne 0 ]; then
      if schedule_force_redo; then
        echo "   ⚠ $tag — Agy controller exit $agy_status, re-run --force-redo"
        continue
      fi
      die "$tag — Agy controller thất bại sau 3 lần (exit $agy_status); không nghiệm thu artifact."
    fi

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
      if schedule_force_redo; then echo "   ⚠ $tag — thiếu output, re-run"; continue; fi
      die "$tag — thiếu/rỗng ${local_stem}_image_prompts.txt sau $full_attempts lần full generation (chạy lại để resume)."
    fi
    if [ "${VP_NO_MUSIC:-0}" != "1" ] && [ ! -s "${local_stem}_music_prompts.txt" ]; then
      if schedule_force_redo; then echo "   ⚠ $tag — thiếu music output, re-run"; continue; fi
      die "$tag — thiếu/rỗng ${local_stem}_music_prompts.txt sau $full_attempts lần full generation (chạy lại để resume)."
    fi
    if [ ! -s "${local_stem}_qa.txt" ]; then
      if schedule_force_redo; then echo "   ⚠ $tag — thiếu QA output, re-run"; continue; fi
      die "$tag — thiếu/rỗng ${local_stem}_qa.txt sau $full_attempts lần full generation (chạy lại để resume)."
    fi
    if [ "${VP_NO_VIDEO:-0}" != "1" ] && [ ! -s "${local_stem}_video_prompts.txt" ]; then
      if schedule_force_redo; then echo "   ⚠ $tag — thiếu video output, re-run"; continue; fi
      die "$tag — thiếu/rỗng ${local_stem}_video_prompts.txt sau $full_attempts lần full generation (chạy lại để resume)."
    fi

    # External gate: rejects runtime prompt generators + shallow/boilerplate
    # outputs (the model cannot bypass this). Pass ⇒ legit deep LLM-expanded output.
    if ! python3 "$SKILL_DIR/scripts/check_run_legit.py" \
        --work "$local_dir/.work" --image "${local_stem}_image_prompts.txt" \
        --video "${local_stem}_video_prompts.txt" --skill-dir "$SKILL_DIR" \
        --require-authorship \
        --authorship-log "$local_dir/.work/active-model-authorship.jsonl" \
        --report-json "$legit_report"; then
      legit_repair_signature=$(python3 - "$legit_report" "$similarity_feedback" "$repair_chunk_size" <<'PY'
import json
import re
import sys
import tempfile
from pathlib import Path

report = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
if not report.get('only_boilerplate'):
    raise SystemExit(1)
chunk_size = int(sys.argv[3])
all_scene_ids = []
for raw_id in report.get('boilerplate_scene_ids', []):
    scene_id = str(raw_id).strip()
    if re.fullmatch(r'\d+[a-zA-Z]?', scene_id) and scene_id not in all_scene_ids:
        all_scene_ids.append(scene_id)
scene_ids = all_scene_ids[:chunk_size]
if not scene_ids:
    raise SystemExit(1)
feedback_path = Path(sys.argv[2])
with tempfile.NamedTemporaryFile(
    mode='w', encoding='utf-8', dir=feedback_path.parent, delete=False,
) as feedback:
    feedback.write('# Legitimacy repair feedback\n\n')
    feedback.write('Rewrite only the listed image scenes. Keep each source anchor exact once in Story DNA, then use distinct visual wording in every other field. Do not repeat any 8-word phrase within one scene.\n\n')
    feedback.write('image_rewrite_scene_ids: ' + ', '.join(scene_ids) + '\n')
temporary_path = Path(feedback.name)
temporary_path.replace(feedback_path)
print('legit:' + str(len(all_scene_ids)) + ':' + ','.join(scene_ids))
PY
      )
      legit_feedback_status=$?
      if [ "$legit_feedback_status" -eq 0 ]; then
        schedule_targeted_repair "$legit_repair_signature"
        targeted_status=$?
        if [ "$targeted_status" -eq 0 ]; then
          echo "   ⚠ $tag — boilerplate feedback, re-run targeted scenes"
          continue
        fi
        [ "$targeted_status" -eq 2 ] \
          && echo "   ⚠ $tag — targeted boilerplate repair không tiến triển, chuyển full retry"
      fi
      if schedule_force_redo; then
        echo "   ⚠ $tag — gate FAIL (bypass/shallow), re-run --force-redo"
        continue
      fi
      die "$tag — gate vẫn FAIL sau $max_full_attempts lần full generation hoặc $max_targeted_repairs repair batches (model bypass expander). Output bị từ chối — chạy lại để resume."
    fi

    grounding_json=$(python3 "$SKILL_DIR/scripts/validate_scene_plan.py" \
      --plan "$local_dir/.work/scene-plan.md" \
      --chapters-json "$local_dir/.work/chapters_qa.json")
    grounding_status=$?
    printf '%s\n' "$grounding_json"
    if [ "$grounding_status" -ne 0 ]; then
      if schedule_force_redo; then echo "   ⚠ $tag — grounding/variation FAIL, re-run --force-redo"; continue; fi
      die "$tag — grounding/variation vẫn FAIL sau $max_full_attempts lần full generation. Output bị từ chối."
    fi

    scene_artifact_json=$(python3 "$SKILL_DIR/scripts/validate_artifacts.py" \
      --check scenes --work-dir "$local_dir/.work" \
      --scene-plan "$local_dir/.work/scene-plan.md")
    scene_artifact_status=$?
    printf '%s\n' "$scene_artifact_json"
    if [ "$scene_artifact_status" -ne 0 ]; then
      if schedule_force_redo; then echo "   ⚠ $tag — scene artifacts FAIL, re-run --force-redo"; continue; fi
      die "$tag — scene artifacts vẫn FAIL sau $max_full_attempts lần full generation. Output bị từ chối."
    fi
    expected_image_count=$(printf '%s\n' "$scene_artifact_json" | python3 -c \
      'import json,sys; print(json.load(sys.stdin)["results"][0]["expected"])' 2>/dev/null)
    expected_video_count=$(printf '%s\n' "$scene_artifact_json" | python3 -c \
      'import json,sys; print(json.load(sys.stdin)["results"][0]["videos_expected"])' 2>/dev/null)
    if ! [[ "$expected_image_count" =~ ^[0-9]+$ && "$expected_video_count" =~ ^[0-9]+$ ]]; then
      if schedule_force_redo; then echo "   ⚠ $tag — scene artifact JSON lỗi, re-run"; continue; fi
      die "$tag — scene artifact JSON không hợp lệ."
    fi

    expected_music_count=0
    if [ "${VP_NO_MUSIC:-0}" != "1" ]; then
      music_artifact_json=$(python3 "$SKILL_DIR/scripts/validate_artifacts.py" \
          --check music --work-dir "$local_dir/.work" --expected-music "$MUSIC" \
          --music-plan "$local_dir/.work/music-plan.md")
      music_artifact_status=$?
      printf '%s\n' "$music_artifact_json"
      if [ "$music_artifact_status" -ne 0 ]; then
        if schedule_force_redo; then echo "   ⚠ $tag — music artifacts FAIL, re-run --force-redo"; continue; fi
        die "$tag — music artifacts vẫn FAIL sau $max_full_attempts lần full generation. Output bị từ chối."
      fi
      expected_music_count=$(printf '%s\n' "$music_artifact_json" | python3 -c \
        'import json,sys; print(json.load(sys.stdin)["results"][0]["expected"])' 2>/dev/null)
      if ! [[ "$expected_music_count" =~ ^[0-9]+$ ]]; then
        if schedule_force_redo; then echo "   ⚠ $tag — không đọc được expected music count, re-run"; continue; fi
        die "$tag — music artifact JSON không hợp lệ."
      fi
    fi

    sim_image_json=$(python3 "$SKILL_DIR/scripts/check_prompt_similarity.py" \
      --image "${local_stem}_image_prompts.txt")
    sim_image=$?
    sim_video_json=''
    sim_video=0
    if [ -s "${local_stem}_video_prompts.txt" ]; then
      sim_video_json=$(python3 "$SKILL_DIR/scripts/check_prompt_similarity.py" \
        --video "${local_stem}_video_prompts.txt")
      sim_video=$?
    fi
    sim_music_json=''
    sim_music=0
    if [ "${VP_NO_MUSIC:-0}" != "1" ]; then
      sim_music_json=$(python3 "$SKILL_DIR/scripts/check_prompt_similarity.py" \
        --music "${local_stem}_music_prompts.txt")
      sim_music=$?
    fi
    for sim_json in "$sim_image_json" "$sim_video_json" "$sim_music_json"; do
      [ -n "$sim_json" ] || continue
      printf '%s\n' "$sim_json" | python3 -c \
        'import json,sys; d=json.load(sys.stdin); print("   similarity: {} violation(s), {} warning(s)".format(len(d.get("violations", [])), len(d.get("warnings", []))))' \
        2>/dev/null || echo "   similarity: output JSON không parse được"
    done
    if [ "$sim_image" -eq 2 ] || [ "$sim_video" -eq 2 ] || [ "$sim_music" -eq 2 ]; then
      sim_image_report="$driver_state/similarity-image.json"
      sim_video_report="$driver_state/similarity-video.json"
      sim_music_report="$driver_state/similarity-music.json"
      printf '%s\n' "$sim_image_json" > "$sim_image_report"
      printf '%s\n' "$sim_video_json" > "$sim_video_report"
      printf '%s\n' "$sim_music_json" > "$sim_music_report"
      similarity_repair_signature=$(python3 - "$similarity_feedback" "$repair_chunk_size" \
          "$sim_image_report" "$sim_video_report" "$sim_music_report" <<'PY'
import json
import re
import sys
import tempfile
from pathlib import Path

feedback_path = Path(sys.argv[1])
chunk_size = int(sys.argv[2])
reports = zip(('image', 'video', 'music'), map(Path, sys.argv[3:]))
keys = {
    'image': 'image_rewrite_scene_ids',
    'video': 'video_rewrite_scene_ids',
    'music': 'music_rewrite_loop_ids',
}
remaining = chunk_size
selected = []
violation_count = 0
for kind, report_path in reports:
    try:
        report = json.loads(report_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        continue
    if not report.get('violations'):
        continue
    violation_count += len(report['violations'])
    ids = []
    for raw_id in report.get('rewrite_scene_ids', []):
        item_id = str(raw_id).strip()
        if re.fullmatch(r'\d+[a-zA-Z]?', item_id) and item_id not in ids:
            ids.append(item_id)
    if ids and remaining:
        chunk = ids[:remaining]
        selected.append((kind, chunk, len(ids)))
        remaining -= len(chunk)

if not selected:
    raise SystemExit(1)
with tempfile.NamedTemporaryFile(
    mode='w', encoding='utf-8', dir=feedback_path.parent, delete=False,
) as feedback:
    feedback.write('# Similarity repair feedback\n\n')
    feedback.write(
        'Rewrite only the listed artifacts. Preserve source grounding and do '
        'not reuse prior phrasing as a template.\n\n'
    )
    for kind, ids, total in selected:
        feedback.write(f'## {kind} gate\n')
        feedback.write(f'repair batch: {len(ids)} of {total} flagged IDs\n')
        feedback.write(keys[kind] + ': ' + ', '.join(ids) + '\n\n')
temporary_path = Path(feedback.name)
temporary_path.replace(feedback_path)
signature_parts = [f'{kind}:{",".join(ids)}' for kind, ids, _ in selected]
print('similarity:' + str(violation_count) + ':' + '|'.join(signature_parts))
PY
      )
      similarity_feedback_status=$?
      if [ "$similarity_feedback_status" -eq 0 ]; then
        schedule_targeted_repair "$similarity_repair_signature"
        targeted_status=$?
        if [ "$targeted_status" -eq 0 ]; then
          echo "   ⚠ $tag — similarity FAIL, re-run targeted batch không --force-redo"
          continue
        fi
        [ "$targeted_status" -eq 2 ] \
          && echo "   ⚠ $tag — targeted similarity repair không tiến triển, chuyển full retry"
      fi
      if schedule_force_redo; then
        echo "   ⚠ $tag — similarity feedback không tạo được hoặc đã hết repair batch, re-run --force-redo"
        continue
      fi
      die "$tag — similarity vẫn FAIL sau $max_full_attempts lần full generation hoặc $max_targeted_repairs repair batches. Output bị từ chối — chạy lại để resume."
    fi
    if [ "$sim_image" -ne 0 ] || [ "$sim_video" -ne 0 ] || [ "$sim_music" -ne 0 ]; then
      if schedule_force_redo; then echo "   ⚠ $tag — similarity gate lỗi I/O, re-run --force-redo"; continue; fi
      die "$tag — similarity gate lỗi sau $max_full_attempts lần full generation. Output bị từ chối."
    fi

    mutation_failed=0
    bible_file="$HOME/.gemini/bibles/$SERIES.md"
    for kind in image video; do
      pf="${local_stem}_${kind}_prompts.txt"
      [ -s "$pf" ] || continue
      if [ -f "$bible_file" ]; then
        python3 "$SKILL_DIR/scripts/check_anchor_consistency.py" \
          --bible "$bible_file" --output "$pf" --fix
        [ "$?" -eq 0 ] || mutation_failed=1
      fi
      safety_output=$(python3 "$SKILL_DIR/scripts/check_content_safety.py" \
        --blocklist "$SKILL_DIR/references/blocklist-content-safety.md" \
        --output "$pf" --fix)
      safety_status=$?
      printf '%s\n' "$safety_output"
      if [ "$safety_status" -eq 2 ]; then
        safety_hits=$(printf '%s\n' "$safety_output" | grep -E '^  .+:' || true)
        blocking_safety=$(printf '%s\n' "$safety_hits" | grep -v ' (WARN-only):' || true)
        [ -n "$safety_hits" ] && [ -z "$blocking_safety" ] || mutation_failed=1
      elif [ "$safety_status" -ne 0 ]; then
        mutation_failed=1
      fi
    done
    if [ "$mutation_failed" -ne 0 ]; then
      if schedule_force_redo; then echo "   ⚠ $tag — anchor/safety fix lỗi, re-run --force-redo"; continue; fi
      die "$tag — anchor/safety fix lỗi sau $max_full_attempts lần full generation. Output bị từ chối."
    fi

    if ! python3 "$SKILL_DIR/scripts/validate_artifacts.py" \
        --check outputs --input "$local_in" \
        --scene-plan "$local_dir/.work/scene-plan.md" \
        --image-count "$expected_image_count" --video-count "$expected_video_count" \
        --music-count "$expected_music_count"; then
      if schedule_force_redo; then echo "   ⚠ $tag — final artifact counts/format FAIL, re-run --force-redo"; continue; fi
      die "$tag — final artifact counts/format vẫn FAIL sau 3 lần."
    fi

    final_sim_image=$(python3 "$SKILL_DIR/scripts/check_prompt_similarity.py" \
      --image "${local_stem}_image_prompts.txt")
    final_sim_status=$?
    if [ -s "${local_stem}_video_prompts.txt" ]; then
      python3 "$SKILL_DIR/scripts/check_prompt_similarity.py" \
        --video "${local_stem}_video_prompts.txt" >/dev/null
      [ "$?" -eq 0 ] || final_sim_status=2
    fi
    if [ "$final_sim_status" -ne 0 ]; then
      if schedule_force_redo; then echo "   ⚠ $tag — final similarity FAIL sau safety, re-run --force-redo"; continue; fi
      die "$tag — file sau safety không qua similarity gate."
    fi

    redo_ok=1
    break
  done
  [ "$redo_ok" = "1" ] || die "$tag — run không hợp lệ"

  # Copy the gated outputs back to the gdrive folder (only the final _*.txt; .work
  # scratch stays local). QA and image are required; music and video depend on mode.
  cp "${local_stem}_image_prompts.txt" "${stem}_image_prompts.txt" \
    || die "$tag — không copy được _image_prompts.txt về $FOLDER"
  if [ "${VP_NO_MUSIC:-0}" != "1" ]; then
    cp "${local_stem}_music_prompts.txt" "${stem}_music_prompts.txt" \
      || die "$tag — không copy được _music_prompts.txt về $FOLDER"
  fi
  cp "${local_stem}_qa.txt" "${stem}_qa.txt" \
    || die "$tag — không copy được _qa.txt về $FOLDER"
  if [ "${VP_NO_VIDEO:-0}" != "1" ]; then
    cp "${local_stem}_video_prompts.txt" "${stem}_video_prompts.txt" \
      || die "$tag — không copy được _video_prompts.txt về $FOLDER"
  fi
  if [ "${VP_NO_MUSIC:-0}" != "1" ]; then
    mkdir -p "$music_cache"
    cp "$local_dir/.work/music-plan.md" "$music_cache/music-plan.md" \
      || die "$tag — không lưu được music-plan cache"
    cache_index=1
    while [ "$cache_index" -le "$expected_music_count" ]; do
      printf -v cache_name 'music-%03d.md' "$cache_index"
      cp "$local_dir/.work/$cache_name" "$music_cache/$cache_name" \
        || die "$tag — không lưu được $cache_name"
      cache_index=$((cache_index + 1))
    done
  fi
  history_path="$HOME/.gemini/bibles/${SERIES}-visual-history.md"
  history_music_args=(--music "${local_stem}_music_prompts.txt")
  [ "${VP_NO_MUSIC:-0}" = "1" ] && history_music_args=()
  python3 "$SKILL_DIR/scripts/check_prompt_similarity.py" --extract-history \
      --image "${local_stem}_image_prompts.txt" \
      "${history_music_args[@]}" --history "$history_path" \
    || die "$tag — output đã copy nhưng không cập nhật được visual history; manifest chưa ghi."
  completion_manifest write "$complete_manifest" "$f" \
      "${stem}_image_prompts.txt" "${stem}_music_prompts.txt" "${stem}_qa.txt" \
      "$video_output" "$music_cache/music-plan.md" "$SKILL_DIR" "$SERIES" \
      "$STYLE" "$MODEL" "$MUSIC" "${VP_NO_VIDEO:-0}" "${VP_NO_MUSIC:-0}" \
    || die "$tag — output đã copy nhưng không ghi được completion manifest."
  rm -rf "$local_dir" "$workers_base"   # local scratch no longer needed; gdrive has the outputs
  echo "✅ $tag — xong (chạy local, đã copy output về gdrive)"
done

echo "✔ Hoàn tất bộ: $SERIES"
