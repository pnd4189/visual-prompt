#!/usr/bin/env python3
"""Assemble image prompts and explicitly enabled optional media prompts.

Reads `<work-dir>/scene-*.md` (each with frontmatter + `## Image Prompt` and
optional `## Video Prompt` blocks).

Always writes next to the input:
    <input-stem>_image_prompts.txt

When explicitly enabled, also writes:
    <input-stem>_video_prompts.txt
    <input-stem>_music_prompts.txt

Separator uses ORIGINAL scene index so video file shows gaps:
    --- SCENE 007 ---
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_SCRIPT_DIR = str(Path(__file__).parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from _io_utils import atomic_write_text, read_text_checked  # type: ignore

_SCENE_NUM_RE = re.compile(r'scene-(\d+[a-zA-Z]?)\.md$')
_MUSIC_NUM_RE = re.compile(r'music-(\d+)\.md$')
_IMAGE_RE = re.compile(
    r'^##\s*Image\s+Prompt\s*\n(.*?)(?=^##\s|\Z)', re.DOTALL | re.MULTILINE
)
_VIDEO_RE = re.compile(
    r'^##\s*Video\s+Prompt\s*\n(.*?)(?=^##\s|\Z)', re.DOTALL | re.MULTILINE
)
_FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)

# --- Depth-gate config -------------------------------------------------------
# Google Flow / Veo3 hard-reject video prompts over 4000 chars; 3800 leaves margin
# for counting drift. This is the binding limit (replaces the old 900-word cap).
VIDEO_CHAR_CAP = 3800
IMAGE_WORD_MIN = 350
IMAGE_WORD_MAX = 650
# Layers 1+3+4 of the negative list are always-include = 19 items; floor 20 catches
# truncation without false positives (cap stays 28).
NEGATIVE_MIN = 20

_IMAGE_HEADERS = ['Camera', 'Story DNA', 'Setting', 'Composition', 'Subject',
                  'Action / Energy', 'Style', 'Lighting / Color', 'Atmosphere', 'Negative']
# --lean: who, where, what — plus the series style lock and the safety negatives.
# The image model supplies camera, light and mood, so the word floor drops with it.
_LEAN_IMAGE_HEADERS = ['Subject', 'Setting', 'Action', 'Style', 'Negative']
LEAN_IMAGE_WORD_MIN = 60
LEAN_IMAGE_WORD_MAX = 220
_VIDEO_HEADERS = ['Cinematography', 'Subject', 'Action', 'Context', 'Style & Ambiance']
_TIMESTAMP_RE = re.compile(r'(?:\[\d{2}:\d{2}|Beat\s*\d+)')
_NEGATIVE_SECTION_RE = re.compile(r'(?ims)^Negative\s*:\s*(.*?)\Z')


def _header_pattern(h: str) -> re.Pattern:
    # 1. Normalize slashes in h to allow optional spacing, e.g. "Action / Energy" or "Action/Energy"
    parts = re.split(r'\s*/\s*', h)
    escaped_parts = [re.escape(p) for p in parts]
    content_pattern = r'\s*/\s*'.join(escaped_parts)
    
    # 2. Allow optional list markers, markdown stars, square brackets, parenthesized notes, and colons in any order
    pattern = r'(?im)^\s*(?:[-*+]\s+)?(?:\*\*|\*|)?\s*(?:\[|)?\s*' + content_pattern + r'\s*(?:\]|)?\s*(?:\s*\([^)]*\))?\s*(?:\*\*|\*|)?\s*(?::|：)?\s*(?:\*\*|\*|)?'
    return re.compile(pattern)


def _missing_headers(block: str, headers: list[str]) -> list[str]:
    missing = []
    for h in headers:
        pattern = _header_pattern(h)
        if not pattern.search(block):
            missing.append(h)
    return missing


def _body_word_count(block: str, headers: list[str]) -> int:
    """Body words excluding the section labels (matches the expander self-check)."""
    stripped = block
    for h in headers:
        pattern = _header_pattern(h)
        stripped = pattern.sub('', stripped)
    return len(stripped.split())


def check_image(block: str, lean: bool = False) -> list[str]:
    problems: list[str] = []
    headers = _LEAN_IMAGE_HEADERS if lean else _IMAGE_HEADERS
    word_min = LEAN_IMAGE_WORD_MIN if lean else IMAGE_WORD_MIN
    word_max = LEAN_IMAGE_WORD_MAX if lean else IMAGE_WORD_MAX
    missing = _missing_headers(block, headers)
    if missing:
        problems.append(f"missing image header(s): {', '.join(missing)}")
    wc = _body_word_count(block, headers)
    if wc < word_min:
        problems.append(f"image body too short: {wc} words (<{word_min})")
    elif wc > word_max:
        problems.append(f"image body too long: {wc} words (>{word_max})")
    # Clean up markdown formatting when checking negative list
    block_clean = re.sub(r'\*+', '', block)
    m = _NEGATIVE_SECTION_RE.search(block_clean)
    neg_count = len([x for x in m.group(1).split(',') if x.strip()]) if m else 0
    if neg_count < NEGATIVE_MIN:
        problems.append(f"negative list too thin: {neg_count} items (<{NEGATIVE_MIN})")
    return problems


def check_video(block: str) -> list[str]:
    problems: list[str] = []
    missing = _missing_headers(block, _VIDEO_HEADERS)
    if missing:
        problems.append(f"missing video header(s): {', '.join(missing)}")
    beats = len(_TIMESTAMP_RE.findall(block))
    if beats < 2 or beats > 3:
        problems.append(f"video beat count out of range: {beats} (need 2-3)")
    if len(block) > VIDEO_CHAR_CAP:
        problems.append(f"video prompt too long: {len(block)} chars (>{VIDEO_CHAR_CAP})")
    return problems


def _scene_num(path: Path) -> str:
    m = _SCENE_NUM_RE.search(path.name)
    return m.group(1) if m else '0'


def _scene_sort_key(path: Path) -> tuple[int, str]:
    val = _scene_num(path)
    num_part = ''
    letter_part = ''
    for char in val:
        if char.isdigit():
            num_part += char
        else:
            letter_part += char
    return (int(num_part) if num_part else 0, letter_part)


def discover_scenes(work_dir: Path) -> list[Path]:
    paths = [p for p in work_dir.glob('scene-*.md') if _SCENE_NUM_RE.fullmatch(p.name)]
    return sorted(paths, key=_scene_sort_key)


def _music_num(path: Path) -> int:
    m = _MUSIC_NUM_RE.search(path.name)
    return int(m.group(1)) if m else 0


def discover_music(work_dir: Path) -> list[Path]:
    paths = [p for p in work_dir.glob('music-*.md') if _MUSIC_NUM_RE.fullmatch(p.name)]
    return sorted(paths, key=_music_num)


def parse_music(path: Path) -> dict:
    """The whole body after frontmatter is the Lyria prompt block (incl. label)."""
    text = read_text_checked(path)
    body = _FRONTMATTER_RE.sub('', text, count=1)
    return {
        'loop_index': _music_num(path),
        'body': body.strip(),
        'path': str(path),
    }


def parse_scene(path: Path) -> dict:
    text = read_text_checked(path)
    body = _FRONTMATTER_RE.sub('', text, count=1)
    img_m = _IMAGE_RE.search(body)
    vid_m = _VIDEO_RE.search(body)
    return {
        'scene_id': _scene_num(path),
        'image': img_m.group(1).strip() if img_m else '',
        'video': vid_m.group(1).strip() if vid_m else '',
        'path': str(path),
    }


def assemble(input_path: Path, work_dir: Path, no_video: bool = True,
             no_music: bool = True, lean: bool = False) -> dict:
    scenes_paths = discover_scenes(work_dir)
    if not scenes_paths:
        raise RuntimeError(f"No scene-*.md found in {work_dir}")

    image_blocks: list[tuple[str, str]] = []
    video_blocks: list[tuple[str, str]] = []
    warnings: list[str] = []
    violations: list[dict] = []

    for sp in scenes_paths:
        sc = parse_scene(sp)
        if not sc['image']:
            warnings.append(f"scene-{sc['scene_id']}.md missing '## Image Prompt' block — skipped")
            continue
        image_blocks.append((sc['scene_id'], sc['image']))
        for detail in check_image(sc['image'], lean):
            violations.append({'scene_id': sc['scene_id'], 'kind': 'image', 'detail': detail})
        if sc['video'] and not no_video:
            video_blocks.append((sc['scene_id'], sc['video']))
            for detail in check_video(sc['video']):
                violations.append({'scene_id': sc['scene_id'], 'kind': 'video', 'detail': detail})

    def _join(blocks: list[tuple[str, str]]) -> str:
        parts = []
        for sid, body in blocks:
            sid_str = f"{int(sid):03d}" if sid.isdigit() else sid
            parts.append(f"--- SCENE {sid_str} ---\n\n{body}")
        return '\n\n'.join(parts)

    output_dir = input_path.parent
    stem = input_path.stem
    img_path = output_dir / f"{stem}_image_prompts.txt"
    vid_path = output_dir / f"{stem}_video_prompts.txt"

    atomic_write_text(img_path, _join(image_blocks))
    if not no_video:
        atomic_write_text(vid_path, _join(video_blocks))

    # Music is opt-in and independent from image/video assembly.
    music_blocks: list[str] = []
    if not no_music:
        for mp in discover_music(work_dir):
            mc = parse_music(mp)
            if mc['body']:
                music_blocks.append(mc['body'])
            else:
                warnings.append(f"{mp.name} has empty body — skipped")

    music_path = None
    if music_blocks:
        music_path = output_dir / f"{stem}_music_prompts.txt"
        atomic_write_text(music_path, '\n\n'.join(music_blocks) + '\n')

    return {
        'image_count': len(image_blocks),
        'video_count': len(video_blocks),
        'video_indices': [sid for sid, _ in video_blocks],
        'image_path': str(img_path),
        'video_path': str(vid_path) if not no_video else None,
        'music_count': len(music_blocks),
        'music_path': str(music_path) if music_path else None,
        'no_video': no_video,
        'no_music': no_music,
        'warnings': warnings,
        'violations': violations,
    }


def main() -> int:
    p = argparse.ArgumentParser(description='Assemble final prompt .txt files')
    p.add_argument('--input', required=True,
                   help='Original novel file path (used to derive output stem + dir)')
    p.add_argument('--work-dir', default=None,
                   help='Dir containing scene-*.md (default: <input-dir>/.work)')
    p.set_defaults(no_video=True, no_music=True)
    p.add_argument('--video', dest='no_video', action='store_false',
                   help='Include video blocks and write _video_prompts.txt')
    p.add_argument('--no-video', dest='no_video', action='store_true',
                   help='Skip video blocks (default; retained for explicit override)')
    p.add_argument('--music', dest='no_music', action='store_false',
                   help='Include music blocks and write _music_prompts.txt')
    p.add_argument('--lean', action='store_true',
                   help='assemble against the lean prompt spec')
    p.add_argument('--no-music', dest='no_music', action='store_true',
                   help='Skip music blocks (default; retained for explicit override)')
    args = p.parse_args()

    input_path = Path(args.input)
    work_dir = Path(args.work_dir) if args.work_dir else input_path.parent / '.work'

    try:
        summary = assemble(
            input_path, work_dir,
            no_video=args.no_video,
            no_music=args.no_music,
            lean=args.lean,
        )
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
