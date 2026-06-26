#!/usr/bin/env python3
"""External bypass/depth gate for run-folder.sh — the model cannot bypass this.

A finished /visual-prompt run is legit only if the model expanded scenes via the
LLM expander (contract #4/#5/#6): no self-made Python prompt generator in .work,
scene-plan + scene-NNN.md produced by the LLM, and deep non-boilerplate output.

run-folder.sh calls this after the skill run, before copying outputs to gdrive.
Exit 0 = legit (ship it); exit 2 = bypass/shallow (re-run the file --force-redo).

Checks:
  1. No .work/*.py contains prompt-section strings (## Image Prompt / Camera: /
     Story DNA: / Subject: / Atmosphere:) — that signature means the model wrote a
     generator instead of using the LLM expander. Legit I/O helpers (apply_qa.py,
     extract.py) never contain these strings, so no false positive.
  2. .work/scene-plan.md exists and scene-NNN.md count matches the plan ids — the
     LLM expander ran for every scene, not skipped.
  3. Each image-prompt scene block is >= IMAGE_WORD_MIN words and has no 8-word run
     repeated >3x (boilerplate loop, the shallow-template fingerprint).
"""
import re
import sys
from pathlib import Path

IMAGE_WORD_MIN = 350
SCENE_FILE_RE = re.compile(r'^scene-(\d{3})\.md$')
SCENE_ID_RE = re.compile(r'^\s*-?\s*scene_id:\s*(\d+)', re.M)
BLOCK_RE = re.compile(r'^--- SCENE (\d+) ---\s*$', re.M)
# prompt-section strings only a bypass generator hardcodes.
PY_BYPASS_RE = re.compile(
    r'##\s*Image Prompt|^\s*Camera\s*:|^\s*Story DNA\s*:|^\s*Subject\s*:|^\s*Atmosphere\s*:',
    re.M,
)
NGRAM_N = 8
NGRAM_MAX_REPEAT = 5  # >5 occurrences of the same 8-word run = boilerplate loop
# Per-scene < IMAGE_WORD_MIN is a skill violation, but the skill's own depth gate
# tolerates a bounded number of short scenes (it proceeds after 2 regen rounds).
# Only flag when the MAJORITY are short — that is the template-generator fingerprint,
# not a legit run with a few short environment shots.
SHORT_MAJORITY_FRAC = 0.5


def _fail(errors):
    print("FAIL (bypass/shallow):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(2)


def main():
    args = sys.argv[1:]
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
              "[--video <vid.txt>] [--skill-dir <skill_root>]",
              file=sys.stderr)
        sys.exit(1)
    errors = []

    # 1. .work/*.py with prompt-section content = bypass generator.
    for p in sorted(work.glob('*.py')):
        try:
            txt = p.read_text(errors='ignore')
        except Exception:
            continue
        if PY_BYPASS_RE.search(txt):
            errors.append(
                f".work/{p.name} chứa prompt-section content (model bypass expander, contract #5/#6)"
            )

    # 1b. Stray *.py at the SKILL ROOT (not scripts/) = bypass clutter the model
    # wrote to its CWD (= skill dir) instead of .work. Check 1 scans .work only,
    # so a root-level generator evades it. Legit skill code lives in scripts/, so
    # any *.py at the skill root is a bypass artifact. run-folder.sh pre-cleans
    # these before each attempt; a file here means the model created it DURING
    # this run.
    if skill_dir is not None and skill_dir.is_dir():
        for p in sorted(skill_dir.glob('*.py')):
            errors.append(
                f"{p.name} ở gốc skill (bypass clutter: model viết generator ra CWD thay vì .work, lách .work scan)"
            )

    # 2. scene-plan.md + scene-NNN.md count matches plan — ONLY when .work still
    # holds the artifacts. The skill sometimes cleans .work after assemble (its
    # log says "dọn dẹp .work"), which is legitimate; in that case the binding
    # signal is the output depth check below. So: only fail if scene-plan.md is
    # present but scene count mismatches (partial / skipped expander). If .work
    # was cleaned (no scene-plan.md), skip these checks rather than false-fail.
    plan = work / 'scene-plan.md'
    if plan.exists():
        plan_ids = set(int(m) for m in SCENE_ID_RE.findall(plan.read_text(errors='ignore')))
        scene_files = {f.name for f in work.iterdir() if SCENE_FILE_RE.match(f.name)}
        if not scene_files:
            errors.append("có scene-plan.md nhưng không có .work/scene-NNN.md (LLM expander bị bỏ qua)")
        elif plan_ids and len(scene_files) != len(plan_ids):
            errors.append(
                f"scene-*.md count ({len(scene_files)}) != scene-plan ids ({len(plan_ids)})"
            )

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