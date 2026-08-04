#!/usr/bin/env python3
"""Worker manifest gate for the bounded-parallel Pass-2 worker submode.

Deterministic fail-closed checks around the immutable worker manifest that
scripts/run-folder.sh (coordinator) writes before spawning each isolated
Pass-2 worker session (`--worker-manifest` in commands/visual-prompt.toml):

  --validate <manifest.json>            schema + frozen-snapshot hash checks
  --verify-run <manifest.json>          post-run ownership fence on work_dir
  --split --plan <scene-plan.md> --workers N
                                        disjoint contiguous scene-ID ranges

Exit codes: 0 = OK, 2 = fail-closed violation, 1 = IO/usage error.

The coordinator stays the only writer of QA, bible/style/history, completion
markers, and final outputs; a worker may only write its assigned scene files
into its own work_dir. Any schema drift, stale snapshot hash, missing/extra
file, or runtime code under work_dir fails closed.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from validate_artifacts import _scene_filename, _scene_plan_details

_HEX_RE = re.compile(r'^[0-9a-f]{64}$')
_SCENE_ID_RE = re.compile(r'^\d+[a-zA-Z]?$')
# Frozen bundle layout inside snapshot_dir: manifest hash field -> filename.
BUNDLE_FILES = {
    'qa_hash': 'chapters_qa.json',
    'bible_hash': 'character-bible.md',
    'style_hash': 'active-style.md',
    'plan_hash': 'scene-plan.md',
}
HISTORY_FILENAME = 'visual-history.md'


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(path: Path) -> tuple[dict | None, list[str]]:
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f'manifest không đọc/parse được: {exc}']
    if not isinstance(payload, dict):
        return None, ['manifest phải là JSON object']
    return payload, []


def schema_violations(manifest: dict) -> list[str]:
    violations = []
    if manifest.get('schema') != 1:
        violations.append(f"schema phải là 1 (hiện là {manifest.get('schema')!r})")
    worker_id = manifest.get('worker_id')
    if not isinstance(worker_id, str) or not worker_id.strip():
        violations.append('worker_id phải là string khác rỗng')
    scene_ids = manifest.get('scene_ids')
    if not isinstance(scene_ids, list) or not scene_ids:
        violations.append('scene_ids phải là danh sách khác rỗng')
    else:
        for scene_id in scene_ids:
            if not isinstance(scene_id, str) or not _SCENE_ID_RE.fullmatch(scene_id):
                violations.append(f'scene_id sai dạng: {scene_id!r}')
        if len(set(scene_ids)) != len(scene_ids):
            violations.append('scene_ids chứa ID trùng nhau')
    for field in (*BUNDLE_FILES, 'history_hash'):
        value = manifest.get(field)
        if field == 'history_hash':
            if not isinstance(value, str) or (value and not _HEX_RE.fullmatch(value)):
                violations.append('history_hash phải là sha256 hex hoặc chuỗi rỗng')
        elif not isinstance(value, str) or not _HEX_RE.fullmatch(value or ''):
            violations.append(f'{field} phải là sha256 hex 64 ký tự')
    for field in ('snapshot_dir', 'work_dir'):
        value = manifest.get(field)
        if not isinstance(value, str) or not value.strip():
            violations.append(f'{field} phải là đường dẫn khác rỗng')
    if not isinstance(manifest.get('video_enabled'), bool):
        violations.append('video_enabled phải là boolean')
    unknown = set(manifest) - {
        'schema', 'worker_id', 'scene_ids', *BUNDLE_FILES, 'history_hash',
        'snapshot_dir', 'work_dir', 'video_enabled',
    }
    if unknown:
        violations.append(f'manifest chứa key lạ: {sorted(unknown)}')
    return violations


def validate(manifest: dict) -> list[str]:
    violations = schema_violations(manifest)
    if violations:
        return violations
    snapshot = Path(manifest['snapshot_dir'])
    if not snapshot.is_dir():
        return [f'snapshot_dir không tồn tại: {snapshot}']
    for field, filename in BUNDLE_FILES.items():
        bundled = snapshot / filename
        if not bundled.is_file():
            violations.append(f'snapshot thiếu {filename}')
            continue
        if _digest(bundled) != manifest[field]:
            violations.append(f'{filename} stale: hash không khớp {field} trong manifest')
    history_hash = manifest['history_hash']
    history_path = snapshot / HISTORY_FILENAME
    if history_hash:
        if not history_path.is_file():
            violations.append(f'snapshot thiếu {HISTORY_FILENAME} dù history_hash khác rỗng')
        elif _digest(history_path) != history_hash:
            violations.append(f'{HISTORY_FILENAME} stale: hash không khớp history_hash')
    work_dir = Path(manifest['work_dir'])
    if not work_dir.is_dir():
        violations.append(f'work_dir không tồn tại: {work_dir}')
    return violations


def verify_run(manifest: dict) -> tuple[list[str], dict]:
    """Returns (violations, details). details carries missing_scene_ids so the
    coordinator can mount a bounded targeted retry on exactly the absent IDs."""
    violations = validate(manifest)
    if violations:
        return violations, {}
    work_dir = Path(manifest['work_dir'])
    expected = {_scene_filename(scene_id) for scene_id in manifest['scene_ids']}
    actual = sorted(
        path for path in work_dir.rglob('*') if path.is_file()
    )
    actual_names = {path.name for path in actual}
    unexpected = []
    for path in actual:
        if path.parent != work_dir:
            violations.append(
                f'file ngoài ownership (nested): {path.relative_to(work_dir)}'
            )
            unexpected.append(str(path.relative_to(work_dir)))
        elif path.name not in expected:
            violations.append(f'file ngoài ownership: {path.name}')
            unexpected.append(path.name)
    missing = sorted(expected - actual_names)
    for name in missing:
        violations.append(f'thiếu scene file được giao: {name}')
    filename_to_id = {
        _scene_filename(scene_id): scene_id for scene_id in manifest['scene_ids']
    }
    details = {
        'missing_scene_ids': [filename_to_id[name] for name in missing],
        'unexpected_files': unexpected,
    }
    return violations, details


def split_plan(plan_path: Path, workers: int) -> tuple[list[dict], list[str]]:
    try:
        scene_ids, _, plan_errors, _, _ = _scene_plan_details(plan_path)
    except OSError as exc:
        return [], [f'không đọc được scene-plan: {exc}']
    violations = [f'scene-plan: {error}' for error in plan_errors]
    if not scene_ids:
        violations.append('scene-plan không có scene row nào')
        return [], violations
    if len(scene_ids) != len(set(scene_ids)):
        violations.append('scene-plan chứa scene id trùng nhau')
        return [], violations
    count = min(workers, len(scene_ids))
    base, remainder = divmod(len(scene_ids), count)
    ranges = []
    start = 0
    for index in range(count):
        size = base + (1 if index < remainder else 0)
        ranges.append({
            'worker_id': f'w{index + 1}',
            'scene_ids': scene_ids[start:start + size],
        })
        start += size
    return ranges, violations


def main() -> int:
    parser = argparse.ArgumentParser(description='Worker manifest gate')
    parser.add_argument('--validate', metavar='MANIFEST', default=None)
    parser.add_argument('--verify-run', dest='verify_run', metavar='MANIFEST', default=None)
    parser.add_argument('--split', action='store_true')
    parser.add_argument('--plan', default=None)
    parser.add_argument('--workers', type=int, default=0)
    args = parser.parse_args()

    if args.validate:
        manifest, errors = load_manifest(Path(args.validate))
        violations = errors or validate(manifest)
        details = {}
    elif args.verify_run:
        manifest, errors = load_manifest(Path(args.verify_run))
        if errors:
            violations, details = errors, {}
        else:
            violations, details = verify_run(manifest)
    elif args.split:
        if not args.plan:
            print('--split cần --plan <scene-plan.md>', file=sys.stderr)
            return 1
        if args.workers < 1:
            print('--split cần --workers >= 1', file=sys.stderr)
            return 1
        ranges, violations = split_plan(Path(args.plan), args.workers)
        if violations:
            print(json.dumps({'ok': False, 'violations': violations}, ensure_ascii=False))
            return 2
        print(json.dumps({'ok': True, 'workers': ranges}, ensure_ascii=False))
        return 0
    else:
        print('usage: worker_manifest.py --validate <manifest> | '
              '--verify-run <manifest> | --split --plan <plan> --workers N',
              file=sys.stderr)
        return 1

    if violations:
        payload = {'ok': False, 'violations': violations}
        if details:
            payload['details'] = details
        print(json.dumps(payload, ensure_ascii=False))
        return 2
    print(json.dumps({'ok': True}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
