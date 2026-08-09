#!/usr/bin/env python3
"""Detect repeated prompt content and maintain per-series visual history."""
from __future__ import annotations

import argparse
import difflib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from _io_utils import atomic_write_text, exclusive_file_lock, read_text_checked

IMAGE_FIELDS = (
    'Camera', 'Story DNA', 'Setting', 'Composition', 'Subject',
    'Action / Energy', 'Style', 'Lighting / Color', 'Atmosphere', 'Negative',
)
COMPARED_IMAGE_FIELDS = (
    'Camera', 'Story DNA', 'Setting', 'Composition',
    'Action / Energy', 'Lighting / Color', 'Atmosphere',
)
HISTORY_SECTIONS = (
    'camera framings used', 'settings used', 'action motifs used',
    'palettes used',
    'music intros used', 'music tags used',
)
SCENE_RE = re.compile(r'^--- SCENE (\d+[a-zA-Z]?) ---\s*$', re.MULTILINE)
LOOP_RE = re.compile(r'^--- LOOP (\d+) / \d+.*---\s*$', re.MULTILINE)
SECTION_RE = re.compile(r'^##\s+(.+?)\s*$', re.MULTILINE)
WORD_RE = re.compile(r"[\w'-]+", re.UNICODE)
NUMBERED_FILLER_RE = re.compile(r'^(?:word|token|pad|filler)[_-]?\d+$', re.I)
GENERIC_TEMPLATE_RE = re.compile(
    r'\b(?:scene setting based on chapter|padding to bypass|generic cinematic scene)\b',
    re.I,
)
FIELD_PATTERNS = tuple(
    (
        name,
        re.compile(
            rf'^(?:\*\*{re.escape(name)}:\*\*|\*\*{re.escape(name)}\**:|'
            rf'{re.escape(name)}:)\s*(.*)$',
            re.IGNORECASE,
        ),
    )
    for name in IMAGE_FIELDS
)


def _parse_block_id(raw_id: str) -> int | str:
    if raw_id.isdigit():
        return int(raw_id)
    match = re.fullmatch(r'(\d+)([a-zA-Z])', raw_id)
    return f'{int(match.group(1)):03d}{match.group(2).casefold()}' if match else raw_id.casefold()


def _split_blocks(text: str, pattern: re.Pattern[str]) -> list[tuple[int | str, str]]:
    matches = list(pattern.finditer(text))
    blocks = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((_parse_block_id(match.group(1)), text[match.end():end].strip()))
    return blocks


def parse_image(text: str) -> list[dict]:
    scenes = []
    for scene_id, body in _split_blocks(text, SCENE_RE):
        fields: dict[str, str] = {}
        current_field: str | None = None
        for raw_line in body.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            matched = False
            for name, pattern in FIELD_PATTERNS:
                field_match = pattern.match(line)
                if field_match:
                    current_field = name
                    fields[name] = field_match.group(1).strip()
                    matched = True
                    break
            if not matched and current_field:
                fields[current_field] = f'{fields[current_field]}\n{line}'.strip()
        scenes.append({'scene_id': scene_id, 'fields': fields})
    return scenes


def _music_block(loop_id: int, body: str) -> dict:
    paragraph_lines = []
    tag_lines = []
    reading_tags = False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith('tags:'):
            reading_tags = True
            tag_lines.append(stripped.split(':', 1)[1])
        elif stripped and reading_tags:
            tag_lines.append(stripped)
        elif stripped:
            paragraph_lines.append(stripped)
    tags = {
        tag.strip().lower()
        for tag in ','.join(tag_lines).split(',')
        if tag.strip()
    }
    return {
        'scene_id': loop_id,
        'body': body,
        'paragraph': ' '.join(paragraph_lines),
        'tags': tags,
    }


def parse_music(text: str) -> list[dict]:
    legacy_blocks = _split_blocks(text, LOOP_RE)
    if legacy_blocks:
        return [_music_block(int(loop_id), body) for loop_id, body in legacy_blocks]

    loops = []
    pending = []
    for chunk in re.split(r'\n\s*\n', text.strip()):
        if not chunk.strip():
            continue
        pending.append(chunk.strip())
        if chunk.lstrip().lower().startswith('tags:'):
            if len(pending) != 2:
                return []
            loops.append(_music_block(len(loops) + 1, '\n\n'.join(pending)))
            pending = []
    return loops if not pending else []


def _tokens(text: str) -> list[str]:
    normalized = []
    for token in WORD_RE.findall(text):
        if NUMBERED_FILLER_RE.fullmatch(token):
            normalized.append('<filler>')
        elif (len(token) >= 9 and sum(char.isupper() for char in token) >= 2
              and sum(char.islower() for char in token) >= 2):
            normalized.append('<nonce>')
        else:
            normalized.append(token.casefold())
    return normalized


def _tfidf_vectors(tokenized: list[list[str]]) -> tuple[list[dict[str, float]], list[float]]:
    document_frequency: Counter[str] = Counter()
    for tokens in tokenized:
        document_frequency.update(set(tokens))
    total = len(tokenized)
    idf = {
        word: math.log(1 + total / (1 + count))
        for word, count in document_frequency.items()
    }
    vectors = []
    norms = []
    for tokens in tokenized:
        vector = {word: count * idf[word] for word, count in Counter(tokens).items()}
        vectors.append(vector)
        norms.append(math.sqrt(sum(value * value for value in vector.values())))
    return vectors, norms


def _cosine(vectors: list[dict[str, float]], norms: list[float], a: int, b: int) -> float:
    if not norms[a] or not norms[b]:
        return 0.0
    left, right = vectors[a], vectors[b]
    if len(left) > len(right):
        left, right = right, left
    numerator = sum(value * right.get(word, 0.0) for word, value in left.items())
    return numerator / (norms[a] * norms[b])


def _similarities(documents: list[str], soft: float):
    tokenized = [_tokens(document) for document in documents]
    normalized = [' '.join(tokens) for tokens in tokenized]
    vectors, norms = _tfidf_vectors(tokenized)
    for left in range(len(documents)):
        if not normalized[left]:
            continue
        for right in range(left + 1, len(documents)):
            if not normalized[right]:
                continue
            matcher = difflib.SequenceMatcher(None, normalized[left], normalized[right])
            sequence_score = matcher.ratio() if matcher.quick_ratio() >= soft else 0.0
            yield left, right, max(sequence_score, _cosine(vectors, norms, left, right))


def _warning(kind: str, field: str | None, left: int, right: int, score: float) -> dict:
    result = {'type': kind, 'scene_a': left, 'scene_b': right, 'sim': round(score, 4)}
    if field:
        result['field'] = field
    return result


def check_image(scenes: list[dict], soft: float, near: float,
                max_pair_copies: int, max_exact_per_field: int) -> dict:
    warnings = []
    violations = []
    banned_phrases: list[str] = []
    pair_fields: dict[tuple[int, int], list[tuple[str, float, str, str]]] = defaultdict(list)
    exact_pairs: dict[str, list[tuple[int, int, float, str, str]]] = defaultdict(list)
    field_stats = {}

    for scene in scenes:
        all_fields = '\n'.join(scene['fields'].values())
        filler_count = sum(
            NUMBERED_FILLER_RE.fullmatch(token) is not None
            for token in WORD_RE.findall(all_fields)
        )
        reasons = []
        if filler_count >= 20:
            reasons.append(f'numbered filler flood ({filler_count} tokens)')
        if GENERIC_TEMPLATE_RE.search(all_fields):
            reasons.append('generic template phrase')
        if reasons:
            violations.append({
                'type': 'template_junk', 'scene_a': scene['scene_id'],
                'reason': '; '.join(reasons),
            })
            banned_phrases.extend(reasons)

    for field in COMPARED_IMAGE_FIELDS:
        documents = [scene['fields'].get(field, '') for scene in scenes]
        scores = []
        for left_index, right_index, score in _similarities(documents, soft):
            scores.append(score)
            left_id = scenes[left_index]['scene_id']
            right_id = scenes[right_index]['scene_id']
            if score >= near:
                pair_fields[(left_id, right_id)].append(
                    (field, score, documents[left_index], documents[right_index])
                )
            elif score >= soft:
                warnings.append(_warning('field_similarity', field, left_id, right_id, score))
            if score >= 0.995:
                exact_pairs[field].append(
                    (left_id, right_id, score, documents[left_index], documents[right_index])
                )
        field_stats[field] = {
            'avg': round(sum(scores) / len(scores), 4) if scores else 0.0,
            'max': round(max(scores), 4) if scores else 0.0,
            'exact': sum(score >= 0.995 for score in scores),
            'high': sum(score >= soft for score in scores),
            'pairs': len(scores),
        }

    copied_pairs = {
        pair: fields for pair, fields in pair_fields.items() if len(fields) >= 2
    }
    if len(copied_pairs) > max_pair_copies:
        for (left_id, right_id), fields in sorted(copied_pairs.items()):
            violations.append({
                'type': 'pair_copy', 'scene_a': left_id, 'scene_b': right_id,
                'fields': [field for field, *_ in fields],
                'sim': round(max(score for _, score, *_ in fields), 4),
            })
            for _, _, left_text, right_text in fields:
                banned_phrases.extend((left_text, right_text))

    for field, pairs in exact_pairs.items():
        if len(pairs) <= max_exact_per_field:
            continue
        for left_id, right_id, score, left_text, right_text in pairs:
            violations.append(_warning('field_dup_flood', field, left_id, right_id, score))
            banned_phrases.extend((left_text, right_text))

    return {
        'violations': violations,
        'warnings': warnings,
        'stats': {'scene_count': len(scenes), 'fields': field_stats},
        'banned_phrases': banned_phrases,
    }


def _check_text_blocks(blocks: list[dict], soft: float, near: float,
                       kind: str) -> dict:
    violations = []
    warnings = []
    banned_phrases = []
    documents = [block['body'] for block in blocks]
    for left_index, right_index, score in _similarities(documents, soft):
        left_id = blocks[left_index]['scene_id']
        right_id = blocks[right_index]['scene_id']
        if score >= near:
            violations.append(_warning(f'{kind}_copy', None, left_id, right_id, score))
            banned_phrases.extend((documents[left_index], documents[right_index]))
        elif score >= soft:
            warnings.append(_warning(f'{kind}_similarity', None, left_id, right_id, score))
    return {
        'violations': violations,
        'warnings': warnings,
        'stats': {'count': len(blocks)},
        'banned_phrases': banned_phrases,
    }


def check_music(loops: list[dict]) -> dict:
    result = _check_text_blocks(loops, 0.75, 0.75, 'music_body')
    for left in range(len(loops)):
        for right in range(left + 1, len(loops)):
            left_id = loops[left]['scene_id']
            right_id = loops[right]['scene_id']
            left_intro = _tokens(loops[left]['paragraph'])[:8]
            right_intro = _tokens(loops[right]['paragraph'])[:8]
            if len(left_intro) == 8 and left_intro == right_intro:
                result['violations'].append(
                    _warning('music_intro_copy', None, left_id, right_id, 1.0)
                )
                result['banned_phrases'].append(' '.join(left_intro))
            union = loops[left]['tags'] | loops[right]['tags']
            overlap = len(loops[left]['tags'] & loops[right]['tags']) / len(union) if union else 0.0
            if overlap > 0.70:
                result['warnings'].append(
                    _warning('music_tag_overlap', None, left_id, right_id, overlap)
                )
    return result


def _scene_id_sort_key(scene_id: int | str) -> tuple[int, str]:
    match = re.fullmatch(r'(\d+)([a-zA-Z]?)', str(scene_id))
    return (int(match.group(1)), match.group(2).casefold()) if match else (0, str(scene_id))


def _rewrite_scene_ids(violations: list[dict]) -> list[int | str]:
    graph: dict[int | str, set[int | str]] = defaultdict(set)
    standalone = set()
    for violation in violations:
        left = violation.get('scene_a')
        right = violation.get('scene_b')
        if isinstance(left, (int, str)) and isinstance(right, (int, str)):
            graph[left].add(right)
            graph[right].add(left)
        elif isinstance(left, (int, str)):
            standalone.add(left)
    rewrite = []
    unseen = set(graph)
    while unseen:
        start = min(unseen, key=_scene_id_sort_key)
        stack = [start]
        component = set()
        while stack:
            node = stack.pop()
            if node in component:
                continue
            component.add(node)
            stack.extend(graph[node] - component)
        unseen -= component
        keep = min(component, key=_scene_id_sort_key)
        rewrite.extend(component - {keep})
    return sorted(set(rewrite) | standalone, key=_scene_id_sort_key)


def _dedupe_phrases(phrases: list[str]) -> list[str]:
    result = []
    seen = set()
    for phrase in phrases:
        compact = ' '.join(phrase.split())[:160].strip()
        key = compact.casefold()
        if compact and key not in seen:
            seen.add(key)
            result.append(compact)
    return result


def _history_values(image_text: str, music_text: str | None) -> dict[str, list[str]]:
    values = {section: [] for section in HISTORY_SECTIONS}
    for scene in parse_image(image_text):
        fields = scene['fields']
        if fields.get('Camera'):
            values['camera framings used'].append(' '.join(fields['Camera'].split()))
        if fields.get('Setting'):
            sentence = re.split(r'(?<=[.!?])\s+', ' '.join(fields['Setting'].split()), maxsplit=1)[0]
            values['settings used'].append(sentence[:200].rstrip())
        if fields.get('Action / Energy'):
            motif = re.split(r'[,;—–]', ' '.join(fields['Action / Energy'].split()), maxsplit=1)[0]
            values['action motifs used'].append(motif.strip())
        if fields.get('Lighting / Color'):
            palette = re.split(r'[,;—–]', ' '.join(fields['Lighting / Color'].split()), maxsplit=1)[0]
            values['palettes used'].append(palette.strip())
    if music_text:
        for loop in parse_music(music_text):
            intro = ' '.join(_tokens(loop['paragraph'])[:10])
            if intro:
                values['music intros used'].append(intro)
            values['music tags used'].extend(sorted(loop['tags']))
    return values


def update_history(path: Path, new_values: dict[str, list[str]]) -> dict:
    lock_path = path.with_name(f'.{path.name}.lock')
    with exclusive_file_lock(lock_path):
        return _update_history_locked(path, new_values)


def _update_history_locked(path: Path, new_values: dict[str, list[str]]) -> dict:
    text = read_text_checked(path) if path.exists() else '# Visual History\n'
    matches = list(SECTION_RE.finditer(text))
    preamble = text[:matches[0].start()].rstrip() if matches else text.rstrip()
    sections: list[tuple[str, list[str]]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end():end]
        sections.append((match.group(1).strip(), body.rstrip().splitlines()))
    history_names = {name.casefold(): name for name in HISTORY_SECTIONS}
    existing_names = {name.casefold() for name, _ in sections}
    for target in HISTORY_SECTIONS:
        if target.casefold() not in existing_names:
            sections.append((target, []))

    rendered = [preamble or '# Visual History']
    counts = {}
    for name, lines in sections:
        target = history_names.get(name.casefold())
        if target:
            old_values = [line[2:].strip() for line in lines if line.strip().startswith('- ')]
            combined = old_values + new_values[target]
            newest_first = []
            seen = set()
            for value in reversed(combined):
                compact = ' '.join(value.split())
                key = compact.casefold()
                if key and key not in seen:
                    seen.add(key)
                    newest_first.append(compact)
            deduped = list(reversed(newest_first))
            deduped = deduped[-150:]
            lines = [f'- {value}' for value in deduped]
            counts[target] = len(deduped)
        rendered.extend((f'\n## {name}', *lines))
    atomic_write_text(path, '\n'.join(rendered).rstrip() + '\n')
    return counts


def _require_blocks(label: str, text: str, blocks: list[dict]) -> list[dict]:
    if not blocks:
        raise ValueError(f'{label} input contains no parseable blocks')
    block_ids = [block['scene_id'] for block in blocks]
    if len(block_ids) != len(set(block_ids)):
        raise ValueError(f'{label} input contains duplicate block ids')
    return blocks


def _require_image_fields(scenes: list[dict]) -> list[dict]:
    for scene in scenes:
        if not any(scene['fields'].get(field) for field in COMPARED_IMAGE_FIELDS):
            raise ValueError(f'image scene {scene["scene_id"]} has no comparable fields')
    return scenes


def _require_music_content(loops: list[dict]) -> list[dict]:
    for loop in loops:
        if not loop['paragraph'] or not loop['tags']:
            raise ValueError(f'music block {loop["scene_id"]} is incomplete')
    return loops


def _read(path: str | None, label: str) -> str | None:
    if not path:
        return None
    file_path = Path(path)
    try:
        return read_text_checked(file_path)
    except FileNotFoundError as exc:
        raise OSError(f'{label} file not found: {file_path}') from exc


def main() -> int:
    parser = argparse.ArgumentParser(description='Check cross-prompt similarity')
    parser.add_argument('--image')
    parser.add_argument('--music')
    parser.add_argument('--video')
    parser.add_argument('--extract-history', action='store_true')
    parser.add_argument('--history')
    parser.add_argument('--soft', type=float, default=0.60)
    parser.add_argument('--near', type=float, default=0.95)
    parser.add_argument('--max-pair-copies', type=int, default=0)
    parser.add_argument('--max-exact-per-field', type=int, default=4)
    args = parser.parse_args()

    try:
        image_text = _read(args.image, 'image')
        music_text = _read(args.music, 'music')
        video_text = _read(args.video, 'video')
        if args.extract_history:
            if image_text is None or not args.history:
                parser.error('--extract-history requires --image and --history')
            _require_image_fields(_require_blocks('image', image_text, parse_image(image_text)))
            if music_text is not None:
                _require_music_content(
                    _require_blocks('music', music_text, parse_music(music_text))
                )
            counts = update_history(Path(args.history), _history_values(image_text, music_text))
            print(json.dumps({'ok': True, 'history': args.history, 'counts': counts}, ensure_ascii=False))
            return 0
        if image_text is None and music_text is None and video_text is None:
            parser.error('provide at least one of --image, --music, or --video')

        parts = []
        if image_text is not None:
            image_scenes = _require_image_fields(
                _require_blocks('image', image_text, parse_image(image_text))
            )
            parts.append(('image', check_image(
                image_scenes, args.soft, args.near,
                args.max_pair_copies, args.max_exact_per_field,
            )))
        if music_text is not None:
            music_loops = _require_music_content(
                _require_blocks('music', music_text, parse_music(music_text))
            )
            parts.append(('music', check_music(music_loops)))
        if video_text is not None:
            video_blocks = _split_blocks(video_text, SCENE_RE)
            if not video_blocks:
                raise ValueError('video input contains no parseable blocks')
            if len({scene_id for scene_id, _ in video_blocks}) != len(video_blocks):
                raise ValueError('video input contains duplicate block ids')
            if any(not body for _, body in video_blocks):
                raise ValueError('video input contains an empty block')
            parts.append(('video', _check_text_blocks(
                [{'scene_id': scene_id, 'body': body}
                 for scene_id, body in video_blocks],
                args.soft, args.near, 'video',
            )))

        violations = [item for _, part in parts for item in part['violations']]
        warnings = [item for _, part in parts for item in part['warnings']]
        phrases = [item for _, part in parts for item in part['banned_phrases']]
        result = {
            'ok': not violations,
            'violations': violations,
            'warnings': warnings,
            'stats': {name: part['stats'] for name, part in parts},
            'rewrite_scene_ids': _rewrite_scene_ids(violations),
            'banned_phrases': _dedupe_phrases(phrases),
        }
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result['ok'] else 2
    except (OSError, RuntimeError, UnicodeError, ValueError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())
