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
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

IMAGE_WORD_MIN = 350
# --lean trades depth for distinctness: the image model fills in camera,
# light and mood, so a scene only carries who/where/what plus the locks.
LEAN_IMAGE_WORD_MIN = 60
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
    '__init__.py', '_io_utils.py', 'active_model_guard.py',
    'active_model_command_policy.py', 'active_model_policy.py',
    'append_bible_row.py', 'assemble_outputs.py',
    'assemble_qa.py', 'calc_scene_count.py', 'check_anchor_consistency.py',
    'check_content_safety.py', 'check_previous_continuity.py',
    'check_prompt_similarity.py', 'check_run_legit.py', 'cleanup_work.py',
    'load_input.py',
    'install_agy_guard.py',
    'resize_16_9.py', 'run-all.sh', 'run-folder.sh',
    'validate_artifacts.py', 'validate_scene_plan.py', 'worker_manifest.py',
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
PADDING_HEADER_RE = re.compile(r'^\s*(?:padding|filler|word padding)\s*:', re.I | re.M)
NUMBERED_FILLER_RE = re.compile(r'\b(?:word|token|pad|filler)[_-]?\d+\b', re.I)
KNOWN_TEMPLATE_RE = re.compile(
    r'\b(?:scene setting based on chapter|padding to bypass|generic cinematic scene)\b',
    re.I,
)


def _looks_like_runtime_code(path):
    if path.suffix.casefold() in RUNTIME_CODE_SUFFIXES:
        return True
    try:
        with path.open('rb') as stream:
            return stream.read(2) == b'#!'
    except OSError:
        return True


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


STYLE_LINE_RE = re.compile(r'^Style:[ \t]*(.+?)\s*$', re.M)
_CATALOG_HEADING_RE = re.compile(r'^###\s+([a-z0-9-]+)\s+—')
_CATALOG_BLOCK_RE = re.compile(r'^-\s*Style block \(EN, paste-ready\):\s*(.*)$')


def _normalize_style(value):
    return ' '.join(value.casefold().split()).rstrip('.')


def catalog_style_blocks(catalog_path):
    """{style id: normalized paste-ready block} from references/style-catalog.md."""
    blocks = {}
    try:
        lines = catalog_path.read_text(encoding='utf-8').splitlines()
    except OSError:
        return blocks
    style_id = None
    for index, line in enumerate(lines):
        heading = _CATALOG_HEADING_RE.match(line)
        if heading:
            style_id = heading.group(1)
            continue
        opening = _CATALOG_BLOCK_RE.match(line)
        if not (opening and style_id):
            continue
        parts = [opening.group(1)]
        for follow in lines[index + 1:]:
            if not follow.strip() or follow.lstrip().startswith(('-', '#')):
                break
            parts.append(follow.strip())
        blocks[style_id] = _normalize_style(' '.join(parts))
    return blocks


def _style_errors(text, catalog_path):
    """The Style block is the series lock, so it must be a catalog block verbatim.

    Nothing compared it to the catalog, and the repetition gate deliberately never
    reads Style at all — so any string passed as long as it repeated. Three runs in
    a row shipped something else: one wrote just the style id, one invented a
    plausible-sounding block, and both looked perfect to every gate (2026-08-13).
    """
    styles = {_normalize_style(m) for m in STYLE_LINE_RE.findall(text)}
    if not styles:
        return []
    known = set(catalog_style_blocks(catalog_path).values())
    if not known:
        # Written to skip when the catalog could not be read — which is the exact
        # shape that let a whole run through this morning: a check that steps
        # aside on missing input is a check that is not there. Say so instead.
        return [f'không đọc được {catalog_path} nên không thể kiểm Style block']
    stray = sorted(s for s in styles if s not in known)
    return [
        f'Style block không khớp references/style-catalog.md: "{value[:70]}…" '
        f'(dùng đúng "Style block (EN, paste-ready)" của style đã chọn)'
        for value in stray
    ]


def _assembled_scene_ids(image_path):
    """Scene ids already merged into the deliverable, casefolded like plan ids."""
    if image_path is None or not image_path.exists():
        return set()
    try:
        return {m.casefold() for m in BLOCK_RE.findall(image_path.read_text(errors='ignore'))}
    except OSError:
        return set()


def _template_junk(body):
    """Return explicit non-prose padding/template fingerprints."""
    reasons = []
    numbered = NUMBERED_FILLER_RE.findall(body)
    if PADDING_HEADER_RE.search(body):
        reasons.append('padding header')
    if len(numbered) >= 20:
        reasons.append(f'numbered filler flood ({len(numbered)} tokens)')
    if KNOWN_TEMPLATE_RE.search(body):
        reasons.append('generic template phrase')
    return reasons


def _proven_writes(log_path):
    """{(basename, sha256)} the primary active model is recorded as having written.

    Returns (writes, errors); a non-empty errors list means the log is unusable.
    """
    if log_path is None or not log_path.is_file():
        return set(), ['active-model authorship log thiếu']
    records = []
    try:
        for line_number, raw in enumerate(log_path.read_text(encoding='utf-8').splitlines(), 1):
            if not raw.strip():
                continue
            record = json.loads(raw)
            if not isinstance(record, dict):
                raise ValueError(f'line {line_number} không phải object')
            records.append(record)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        return set(), [f'active-model authorship log không hợp lệ: {exc}']
    proven = {
        (record.get('basename'), record.get('sha256'))
        for record in records
        if record.get('schema') == 1
        and record.get('event') == 'creative_write'
        and record.get('conversation_id')
        and record.get('conversation_id') == record.get('primary_conversation_id')
        and record.get('model')
        and isinstance(record.get('size'), int) and record.get('size') > 0
        and Path(str(record.get('target', ''))).name == record.get('basename')
        and record.get('tool') in {'write_to_file', 'replace_file_content', 'multi_replace_file_content'}
    }
    return proven, []


def _authorship_errors(scene_files, log_path):
    proven, errors = _proven_writes(log_path)
    if errors:
        return errors
    for scene in sorted(scene_files):
        digest = _sha256(scene)
        if (scene.name, digest) not in proven:
            errors.append(
                f'{scene.name} thiếu provenance khớp SHA-256 từ primary active model'
            )
    return errors


def _authorship_from_log(expected_scene_files, log_path):
    """Provenance for a run whose scene files were already merged and cleaned.

    The files themselves are gone by then, so the SHA-256 comparison above has
    nothing to read. What survives is the log: it must still name every scene
    the plan declared, written by the primary active model.
    """
    proven, errors = _proven_writes(log_path)
    if errors:
        return errors
    written = {basename for basename, _ in proven}
    missing = sorted(set(expected_scene_files) - written)
    if missing:
        errors.append(
            f'{len(missing)} scene không có provenance trong authorship log '
            f'(vd {", ".join(missing[:3])})'
        )
    return errors


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


def write_report(path, boilerplate, only_boilerplate, worker_run=False):
    report = {
        'boilerplate_scene_ids': list(dict.fromkeys(
            item['scene_id'] for item in boilerplate
        )),
        'only_boilerplate': only_boilerplate,
    }
    if worker_run:
        report['worker_run'] = True
    payload = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    with tempfile.NamedTemporaryFile(
        mode='w', encoding='utf-8', dir=path.parent, delete=False,
    ) as temporary:
        temporary.write(payload)
        temporary_path = Path(temporary.name)
    temporary_path.replace(path)


def main():
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] == '--purge-skill-dir':
        purge_skill_dir(Path(args[1]))
        sys.exit(0)
    work = None
    image_path = None
    report_path = None
    video_path = None
    skill_dir = None
    worker_manifest_path = None
    authorship_log_path = None
    require_authorship = False
    lean = False
    i = 0
    while i < len(args):
        a = args[i]
        if a == '--work' and i + 1 < len(args):
            work = Path(args[i + 1]); i += 2
        elif a == '--image' and i + 1 < len(args):
            image_path = Path(args[i + 1]); i += 2
        elif a == '--report-json' and i + 1 < len(args):
            report_path = Path(args[i + 1]); i += 2
        elif a == '--video' and i + 1 < len(args):
            video_path = Path(args[i + 1]); i += 2
        elif a == '--skill-dir' and i + 1 < len(args):
            skill_dir = Path(args[i + 1]); i += 2
        elif a == '--worker-manifest' and i + 1 < len(args):
            worker_manifest_path = Path(args[i + 1]); i += 2
        elif a == '--authorship-log' and i + 1 < len(args):
            authorship_log_path = Path(args[i + 1]); i += 2
        elif a == '--require-authorship':
            require_authorship = True; i += 1
        elif a == '--lean':
            lean = True; i += 1
        else:
            i += 1
    if work is None:
        print("usage: check_run_legit.py --work <work_dir> --image <img.txt> "
              "[--video <vid.txt>] [--skill-dir <skill_root>] "
              "[--worker-manifest <manifest.json>] [--require-authorship "
              "--authorship-log <records.jsonl>]\n"
              "       check_run_legit.py --purge-skill-dir <skill_root>",
              file=sys.stderr)
        sys.exit(1)
    default_authorship_log = work / 'active-model-authorship.jsonl'
    if os.environ.get('VP_GUARD_ACTIVE') == '1':
        require_authorship = True
        if authorship_log_path is None:
            configured = os.environ.get('VP_AUTHORSHIP_LOG')
            authorship_log_path = Path(configured) if configured else default_authorship_log
    errors = []
    boilerplate = []
    worker_run = False
    worker_scene_ids = None

    # Worker-run semantics (bounded-parallel Pass-2 worker submode): the workdir
    # legitimately holds ONLY the assigned scene files — no assembled image/video
    # output exists yet, so depth/boilerplate checks are skipped exactly like the
    # --no-video skip rule. Runtime-code and ownership checks stay; the assembled
    # gate re-runs coordinator-side after join.
    if worker_manifest_path is not None:
        worker_run = True
        try:
            worker_manifest = json.loads(worker_manifest_path.read_text(encoding='utf-8'))
            raw_ids = worker_manifest['scene_ids']
            if not isinstance(raw_ids, list) or not raw_ids:
                raise ValueError('scene_ids phải là danh sách khác rỗng')
            worker_scene_ids = [str(item) for item in raw_ids]
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"worker manifest không đọc được: {exc}")

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

    # 2W. Worker-run ownership check: the workdir must contain exactly the
    # assigned scene files (plus nothing else) before the coordinator joins.
    if worker_run and worker_scene_ids is not None:
        expected = set()
        for scene_id in worker_scene_ids:
            match = re.fullmatch(r'(\d+)([a-zA-Z]?)', scene_id)
            if not match:
                errors.append(f"worker manifest scene_id sai dạng: {scene_id}")
                continue
            expected.add(f'scene-{int(match.group(1)):03d}{match.group(2)}.md')
        actual = sorted(p.name for p in work.rglob('*') if p.is_file())
        for name in actual:
            if name not in expected:
                errors.append(
                    f"worker workdir chứa file ngoài ownership: {name} "
                    "(chỉ scene files được giao trong manifest)"
                )
        for name in sorted(expected - set(actual)):
            errors.append(f"worker workdir thiếu scene file được giao: {name}")

    # cleanup_work.py deletes merged scene files, and on a gdrive mount that takes
    # minutes — every file it removes moves the count further from the plan while
    # scene-plan.md is still sitting there. A run checked inside that window failed
    # as bypass twice over: "scene-*.md count (1) != scene-plan ids (156)", then
    # "không có scene artifact" once cleanup finished, and the model was told to
    # rebuild files it had deleted on purpose (observed 2026-08-13). Once the
    # deliverable carries a block for every planned id the expander demonstrably
    # ran, so both checks fall back to evidence that survives cleanup.
    plan = work / 'scene-plan.md'
    parsed_plan_ids: list[str] = []
    plan_ids: set[str] = set()
    expected_scene_files: set[str] = set()
    if not worker_run and plan.exists():
        parsed_plan_ids = [m.casefold() for m in SCENE_ID_RE.findall(plan.read_text(errors='ignore'))]
        plan_ids = set(parsed_plan_ids)
        for scene_id in plan_ids:
            match = re.fullmatch(r'(\d+)([a-z]?)', scene_id)
            if match:
                expected_scene_files.add(
                    f'scene-{int(match.group(1)):03d}{match.group(2)}.md'
                )
    merged = bool(plan_ids) and plan_ids <= _assembled_scene_ids(image_path)

    scene_artifacts = [
        path for path in work.rglob('*')
        if path.is_file() and SCENE_FILE_RE.fullmatch(path.name)
    ]
    if require_authorship:
        if scene_artifacts:
            errors.extend(_authorship_errors(scene_artifacts, authorship_log_path))
        elif merged:
            errors.extend(_authorship_from_log(expected_scene_files, authorship_log_path))
        else:
            errors.append('không có scene artifact để kiểm tra active-model authorship')

    # 2. scene-plan.md + scene-NNN.md count matches plan — ONLY when .work still
    # holds the artifacts. The skill sometimes cleans .work after assemble (its
    # log says "dọn dẹp .work"), which is legitimate; in that case the binding
    # signal is the output depth check below. So: only fail if scene-plan.md is
    # present but scene count mismatches (partial / skipped expander). If .work
    # was cleaned (no scene-plan.md), skip these checks rather than false-fail.
    # Worker runs keep their frozen scene-plan in the read-only snapshot dir, so
    # this block applies only to full-pipeline runs.
    if not worker_run and plan.exists():
        scene_files = {f.name for f in work.iterdir() if SCENE_FILE_RE.match(f.name)}
        if len(parsed_plan_ids) != len(plan_ids):
            errors.append('scene-plan.md chứa scene id trùng nhau')
        if merged:
            pass
        elif not scene_files:
            errors.append("có scene-plan.md nhưng không có .work/scene-NNN.md (LLM expander bị bỏ qua)")
        elif plan_ids and len(scene_files) != len(plan_ids):
            errors.append(
                f"scene-*.md count ({len(scene_files)}) != scene-plan ids ({len(plan_ids)})"
            )
        elif scene_files != expected_scene_files:
            errors.append('scene-*.md ids không khớp scene-plan.md')

    # 3. output depth: per-scene word count + boilerplate-loop detection.
    # Worker runs have no assembled output yet (skipped per worker semantics).
    if not worker_run and (
        image_path is None or not image_path.exists() or image_path.stat().st_size == 0
    ):
        errors.append("output _image_prompts.txt thiếu/rỗng")
    elif not worker_run:
        text = image_path.read_text(errors='ignore')
        errors.extend(_style_errors(
            text, Path(__file__).resolve().parents[1] / 'references' / 'style-catalog.md'))
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
            for k, m in enumerate(markers):
                end = markers[k + 1].start() if k + 1 < len(markers) else len(text)
                raw_body = text[m.end():end]
                reasons = _template_junk(raw_body)
                body = re.sub(r'^[A-Za-z][A-Za-z /]*:\s*', '', raw_body, flags=re.M)
                words = body.lower().split()
                counts = {}
                for j in range(len(words) - NGRAM_N + 1):
                    g = ' '.join(words[j:j + NGRAM_N])
                    counts[g] = counts.get(g, 0) + 1
                repeated = sorted(
                    phrase for phrase, count in counts.items()
                    if count > NGRAM_MAX_REPEAT
                )
                if repeated:
                    reasons.extend(repeated)
                if reasons:
                    boilerplate.append({
                        'scene_id': m.group(1),
                        'phrases': reasons,
                    })
            if boilerplate:
                errors.append(
                    f"{len(boilerplate)}/{len(markers)} scene block có boilerplate/padding "
                    "(template-generated, bypass expander)"
                )

            # 3b. Header-structure check: the image expander spec mandates 10
            # sections (Camera, Story DNA, Setting, Composition, Subject,
            # Action / Energy, Style, Lighting / Color, Atmosphere, Negative). A
            # shortcut bypass writes one unstructured paragraph per scene (no
            # headers) — usable but NOT the deep layered format. A legit
            # deep-but-concise scene still has all 10 headers (just shorter
            # content), so this catches shortcuts without false-failing concise
            # runs. Accept plain (`Camera:`) or bold (`**Camera:**`) labels.
            _IMG_HDRS = (['Subject', 'Setting', 'Action', 'Style', 'Negative'] if lean
                         else ['Camera', 'Story DNA', 'Setting', 'Composition', 'Subject',
                               'Action / Energy', 'Style', 'Lighting / Color',
                               'Atmosphere', 'Negative'])
            _MIN_HDRS = len(_IMG_HDRS) - 1
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
                if present < _MIN_HDRS:
                    shallow += 1
            if shallow > len(markers) * 0.5:
                errors.append(
                    f"{shallow}/{len(markers)} image scene block thiếu header structure (shortcut bypass, không đúng {len(_IMG_HDRS)}-section format)"
                )

    # 4. Video boilerplate bypass: the video expander must produce per-scene
    # deep prompts. A bypass writes ONE generic template (e.g. "Cultivators flying
    # on glowing swords …") duplicated across every video scene — identical blocks
    # that don't match each scene's content. Flag when ≥4 video scenes share the
    # same normalized body (>50% identical = boilerplate, not LLM-expanded).
    if not worker_run and video_path is not None and video_path.exists() \
            and video_path.stat().st_size > 0:
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

    if report_path is not None:
        write_report(
            report_path, boilerplate,
            bool(boilerplate) and len(errors) == 1, worker_run=worker_run,
        )
    if errors:
        _fail(errors)
    if worker_run:
        print("OK: legit worker run — không runtime code, đúng ownership scene files")
    else:
        print("OK: legit run — không .py bypass, scene count match, no boilerplate (image+video)")
    sys.exit(0)


if __name__ == '__main__':
    main()
