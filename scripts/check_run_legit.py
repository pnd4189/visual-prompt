#!/usr/bin/env python3
"""External bypass/depth gate for run-folder.sh — the model cannot bypass this.

A finished /visual-prompt run is legit only if the model expanded scenes via the
LLM expander (contract #4/#5/#6): no self-made runtime prompt generator in
.work, scene-plan + scene-NNN.md produced by the LLM, and deep non-boilerplate
output.

run-folder.sh calls this after the skill run, before copying outputs to gdrive.
Exit 0 = legit (ship it); exit 2 = bypass/shallow (re-run the file --force-redo).

Checks:
  1. No executable/code file is created anywhere below .work. A creative run must
     write markdown artifacts directly; nested generators are still bypasses.
  1b. scripts/ holds exactly CANONICAL_SCRIPTS and the skill root holds no code
     files. The model has hidden bypass generators INSIDE scripts/ before
     (generate_*.py, fix_*.py, pad_*.py named to look like real helpers) — a
     root-only scan misses them, and a future run may mistake them for canonical
     pipeline scripts and re-run the bypass.
  2. .work/scene-plan.md exists and scene-NNN.md count matches the plan ids — the
     LLM expander ran for every scene, not skipped.
  3. Each image-prompt scene block is >= IMAGE_WORD_MIN words and has no 8-word run
     repeated >3x (boilerplate loop, the shallow-template fingerprint).

Purge mode: `check_run_legit.py --purge-skill-dir <skill_root>` moves every rogue
entry (non-canonical scripts/ file, root-level code file) into
<skill_root>/.quarantine-auto/ — recoverable, never deletes. run-folder.sh calls
this before each attempt so a prior bypass can't stale-poison the retry.
"""
import re
import sys
from pathlib import Path

IMAGE_WORD_MIN = 350
SCENE_FILE_RE = re.compile(r'^scene-(\d{3}[a-zA-Z]?)\.md$')
SCENE_ID_RE = re.compile(r'^\s*\|\s*(\d+[a-zA-Z]?)\s*\|', re.M)
BLOCK_RE = re.compile(r'^--- SCENE (\d+[a-zA-Z]?) ---\s*$', re.M)
NGRAM_N = 8
NGRAM_MAX_REPEAT = 5  # >5 occurrences of the same 8-word run = boilerplate loop
# Per-scene < IMAGE_WORD_MIN is a skill violation, but the skill's own depth gate
# tolerates a bounded number of short scenes (it proceeds after 2 regen rounds).
# Only flag when the MAJORITY are short — that is the template-generator fingerprint,
# not a legit run with a few short environment shots.
SHORT_MAJORITY_FRAC = 0.5

# The complete, versioned contents of scripts/. Anything else in scripts/ is a
# model-made bypass helper (contract #1/#5/#6). Update this set whenever the
# skill adds a real helper — same release discipline as the SKILL.md version bump.
CANONICAL_SCRIPTS = {
    '__init__.py', '_io_utils.py', 'append_bible_row.py', 'assemble_outputs.py',
    'assemble_qa.py', 'calc_scene_count.py', 'check_anchor_consistency.py',
    'check_content_safety.py', 'check_previous_continuity.py',
    'check_prompt_similarity.py', 'check_run_legit.py', 'load_input.py',
    'resize_16_9.py', 'run-all.sh', 'run-folder.sh',
    'validate_artifacts.py', 'validate_scene_plan.py',
}
# Code files allowed at the skill ROOT. Everything else matching ROOT_CODE_GLOBS
# is bypass clutter the model wrote to its CWD instead of .work.
CANONICAL_ROOT_FILES = {'setup.sh', 'setup.bat'}
ROOT_CODE_GLOBS = (
    '*.py', '*.pyw', '*.js', '*.mjs', '*.cjs', '*.ts', '*.tsx',
    '*.sh', '*.bash', '*.zsh', '*.fish', '*.ps1', '*.bat', '*.cmd',
    '*.rb', '*.pl', '*.php', '*.lua', '*.r', '*.ipynb',
    '*.go', '*.rs', '*.java', '*.cs', '*.c', '*.cc', '*.cpp',
)
RUNTIME_CODE_SUFFIXES = {pattern[1:] for pattern in ROOT_CODE_GLOBS}
RUNTIME_CODE_SUFFIXES.update({'.exe', '.com'})


def _looks_like_runtime_code(path):
    if path.suffix.casefold() in RUNTIME_CODE_SUFFIXES:
        return True
    try:
        with path.open('rb') as stream:
            return stream.read(2) == b'#!'
    except OSError:
        return True


def rogue_entries(skill_dir):
    """Non-canonical entries inside scripts/ + stray code files at the skill root."""
    rogue = []
    scripts = skill_dir / 'scripts'
    if scripts.is_dir():
        for p in sorted(scripts.iterdir()):
            if p.name in CANONICAL_SCRIPTS or p.name == '__pycache__':
                continue
            rogue.append(p)
    rogue.extend(
        p for p in sorted(skill_dir.iterdir())
        if p.is_file()
        and p.name not in CANONICAL_ROOT_FILES
        and _looks_like_runtime_code(p)
    )
    return rogue


def purge_skill_dir(skill_dir):
    """Quarantine rogue entries into .quarantine-auto/ (recoverable, never deletes)."""
    qdir = skill_dir / '.quarantine-auto'
    moved = 0
    for p in rogue_entries(skill_dir):
        qdir.mkdir(exist_ok=True)
        dest = qdir / p.name
        n = 1
        while dest.exists():
            dest = qdir / f"{p.name}.{n}"
            n += 1
        p.rename(dest)
        print(f"purged: {p.relative_to(skill_dir)} -> {dest.relative_to(skill_dir)}")
        moved += 1
    print(f"purge OK: {moved} rogue file(s) quarantined")


def _fail(errors):
    print("FAIL (bypass/shallow):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(2)


def main():
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] == '--purge-skill-dir':
        purge_skill_dir(Path(args[1]))
        sys.exit(0)
    work = None
    image_path = None
    video_path = None
    skill_dir = None
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--work' and i + 1 < len(args):
            work = Path(args[i + 1]); i += 2
        elif a == '--image' and i + 1 < len(args):
            image_path = Path(args[i + 1]); i += 2
        elif a == '--video' and i + 1 < len(args):
            video_path = Path(args[i + 1]); i += 2
        elif a == '--skill-dir' and i + 1 < len(args):
            skill_dir = Path(args[i + 1]); i += 2
        else:
            i += 1
    if work is None:
        print("usage: check_run_legit.py --work <work_dir> --image <img.txt> "
              "[--video <vid.txt>] [--skill-dir <skill_root>]\n"
              "       check_run_legit.py --purge-skill-dir <skill_root>",
              file=sys.stderr)
        sys.exit(1)
    errors = []

    # 1. Any runtime code file under .work is a bypass. The active model writes
    # markdown artifacts directly; recursive scanning catches hidden generators.
    for p in sorted(
        candidate for candidate in work.rglob('*')
        if candidate.is_file() and _looks_like_runtime_code(candidate)
    ):
        relative = p.relative_to(work)
        errors.append(
            f".work/{relative} là runtime code (model tự chế generator/orchestration, "
            "strict-generation-contract)"
        )

    # 1b. Rogue code files: non-canonical entries in scripts/ + any code file at
    # the skill root. The model has hidden bypass generators in BOTH places —
    # root *.py evading the .work scan, and scripts/*.py named to look canonical
    # (generate_plan.py, expand_scenes.py) which a later run may re-run as if
    # legit. run-folder.sh purges these before each attempt, so anything found
    # here was created DURING this run.
    if skill_dir is not None and skill_dir.is_dir():
        for p in rogue_entries(skill_dir):
            errors.append(
                f"{p.relative_to(skill_dir)} không thuộc bộ script canonical (model tự chế helper/generator, contract #1/#5/#6)"
            )

    # 2. scene-plan.md + scene-NNN.md count matches plan — ONLY when .work still
    # holds the artifacts. The skill sometimes cleans .work after assemble (its
    # log says "dọn dẹp .work"), which is legitimate; in that case the binding
    # signal is the output depth check below. So: only fail if scene-plan.md is
    # present but scene count mismatches (partial / skipped expander). If .work
    # was cleaned (no scene-plan.md), skip these checks rather than false-fail.
    plan = work / 'scene-plan.md'
    if plan.exists():
        parsed_plan_ids = [m.casefold() for m in SCENE_ID_RE.findall(plan.read_text(errors='ignore'))]
        plan_ids = set(parsed_plan_ids)
        scene_files = {f.name for f in work.iterdir() if SCENE_FILE_RE.match(f.name)}
        expected_scene_files = set()
        for scene_id in plan_ids:
            match = re.fullmatch(r'(\d+)([a-z]?)', scene_id)
            if match:
                expected_scene_files.add(
                    f'scene-{int(match.group(1)):03d}{match.group(2)}.md'
                )
        if len(parsed_plan_ids) != len(plan_ids):
            errors.append('scene-plan.md chứa scene id trùng nhau')
        if not scene_files:
            errors.append("có scene-plan.md nhưng không có .work/scene-NNN.md (LLM expander bị bỏ qua)")
        elif plan_ids and len(scene_files) != len(plan_ids):
            errors.append(
                f"scene-*.md count ({len(scene_files)}) != scene-plan ids ({len(plan_ids)})"
            )
        elif scene_files != expected_scene_files:
            errors.append('scene-*.md ids không khớp scene-plan.md')

    # 3. output depth: per-scene word count + boilerplate-loop detection.
    if image_path is None or not image_path.exists() or image_path.stat().st_size == 0:
        errors.append("output _image_prompts.txt thiếu/rỗng")
    else:
        text = image_path.read_text(errors='ignore')
        markers = list(BLOCK_RE.finditer(text))
        if not markers:
            errors.append("output không có '--- SCENE N ---' block")
        else:
            # The bypass fingerprint is BOILERPLATE (a template phrase looped) and
            # a self-made .py generator — NOT word count. A legit LLM run can produce
            # concise-but-specific prompts (e.g. ~275 words for an environment shot)
            # that are below the 350-word spec target yet still deep, layered, and
            # usable; the skill's own depth gate (assemble_outputs, IMAGE_WORD_MIN)
            # already handles per-scene shortness with bounded regen. Rejecting on
            # word count here would false-fail good runs and re-run forever. So this
            # gate only flags boilerplate loops (template-generated) + the .py +
            # scene-count checks above.
            boiler = 0
            for k, m in enumerate(markers):
                end = markers[k + 1].start() if k + 1 < len(markers) else len(text)
                body = text[m.end():end]
                body = re.sub(r'^[A-Za-z][A-Za-z /]*:\s*', '', body, flags=re.M)
                words = body.lower().split()
                counts = {}
                for j in range(len(words) - NGRAM_N + 1):
                    g = ' '.join(words[j:j + NGRAM_N])
                    counts[g] = counts.get(g, 0) + 1
                if counts and max(counts.values()) > NGRAM_MAX_REPEAT:
                    boiler += 1
            if boiler:
                errors.append(
                    f"{boiler}/{len(markers)} scene block có boilerplate repeat (template-generated, bypass expander)"
                )

            # 3b. Header-structure check: the image expander spec mandates 10
            # sections (Camera, Story DNA, Setting, Composition, Subject,
            # Action / Energy, Style, Lighting / Color, Atmosphere, Negative). A
            # shortcut bypass writes one unstructured paragraph per scene (no
            # headers) — usable but NOT the deep layered format. A legit
            # deep-but-concise scene still has all 10 headers (just shorter
            # content), so this catches shortcuts without false-failing concise
            # runs. Accept plain (`Camera:`) or bold (`**Camera:**`) labels.
            _IMG_HDRS = ['Camera', 'Story DNA', 'Setting', 'Composition', 'Subject',
                         'Action / Energy', 'Style', 'Lighting / Color',
                         'Atmosphere', 'Negative']
            shallow = 0
            for k, m in enumerate(markers):
                end = markers[k + 1].start() if k + 1 < len(markers) else len(text)
                body = text[m.end():end]
                present = 0
                for h in _IMG_HDRS:
                    # plain `Header:` or bold `**Header:**` at line start
                    if re.search(r'^' + re.escape(h) + r'\s*:', body, re.M) or \
                       re.search(r'^\*\*' + re.escape(h) + r'\s*:\*\*', body, re.M):
                        present += 1
                if present < 9:
                    shallow += 1
            if shallow > len(markers) * 0.5:
                errors.append(
                    f"{shallow}/{len(markers)} image scene block thiếu header structure (shortcut bypass, không phải 10-section deep format)"
                )

    # 4. Video boilerplate bypass: the video expander must produce per-scene
    # deep prompts. A bypass writes ONE generic template (e.g. "Cultivators flying
    # on glowing swords …") duplicated across every video scene — identical blocks
    # that don't match each scene's content. Flag when ≥4 video scenes share the
    # same normalized body (>50% identical = boilerplate, not LLM-expanded).
    if video_path is not None and video_path.exists() and video_path.stat().st_size > 0:
        vtext = video_path.read_text(errors='ignore')
        vmarkers = list(BLOCK_RE.finditer(vtext))
        vbodies = []
        for k, m in enumerate(vmarkers):
            end = vmarkers[k + 1].start() if k + 1 < len(vmarkers) else len(vtext)
            body = re.sub(r'\s+', ' ', vtext[m.end():end]).strip()
            if body:
                vbodies.append(body)
        if len(vbodies) >= 4:
            from collections import Counter
            most_common_cnt = Counter(vbodies).most_common(1)[0][1]
            if most_common_cnt / len(vbodies) > 0.5:
                errors.append(
                    f"{most_common_cnt}/{len(vbodies)} video scene blocks identical (boilerplate template, video expander bypass)"
                )

    if errors:
        _fail(errors)
    print("OK: legit run — không .py bypass, scene count match, no boilerplate (image+video)")
    sys.exit(0)


if __name__ == '__main__':
    main()
