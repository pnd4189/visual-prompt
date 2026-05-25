---
phase: 6
title: "Docs & README"
status: done
priority: P2
effort: "0.5d"
dependencies: [5]
---

# Phase 6: Docs & README

## Overview

User-facing docs in Vietnamese (target audience: VN YouTube creator, not developer). 3 docs total: `HUONG-DAN-SU-DUNG.md` (full step-by-step guide), expanded `README.md` (overview + install + quick start), `antigravity/README.md` (Antigravity-specific install note). Includes troubleshooting section based on real issues from Phase 5 testing.

## Context Links

- Phase 5 test results (informs troubleshooting section)
- Brainstorm §11 (Phase 6 scope)
- Reference: `/home/dung/VIBE_CODING/Grammar_check/chinese-novel-proofreader/HUONG-DAN-SU-DUNG.md` (VN guide pattern)

## Requirements

**Functional:**
- VN user with zero CLI experience can: install skill (1 command) + run `/visual-prompt` (1 command) + paste outputs into Gemini/Veo3 (clear instructions)
- Troubleshooting covers top 5 real issues from Phase 5 testing
- Cross-file series workflow documented with explicit `--series` example
- Output paste instructions per AI tool (Gemini/Qwen/ChatGPT/Veo3/Seedance) — show where to paste, what to expect

**Non-functional:**
- `HUONG-DAN-SU-DUNG.md` ≤500 lines; readable in ~10 min by non-developer
- `README.md` ≤150 lines (skimmable for GitHub landing)
- Vietnamese throughout user-facing copy; preserve English technical terms (slash command names, file paths)
- Screenshots optional but slot reserved (markdown image refs to `docs/img/`)

## Architecture

```
visual-prompt/
├── README.md                       # EXPANDED from Phase 1 skeleton — VN overview + install + 3-line quickstart + links
├── HUONG-DAN-SU-DUNG.md           # NEW — full VN user guide
└── antigravity/
    └── README.md                  # NEW — Antigravity-specific install note (Windows admin caveat, etc.)
```

## Related Code Files

### Create
- `HUONG-DAN-SU-DUNG.md` — sections:
  1. Skill này làm gì? (1 paragraph)
  2. Yêu cầu (Antigravity CLI, Python 3.10+, Gemini Ultra)
  3. Cài đặt (Linux/Mac 1 lệnh, Windows 2 cách: admin + non-admin)
  4. Sử dụng cơ bản: `/visual-prompt <file.txt>` — kết quả là gì, file nằm ở đâu
  5. Sử dụng nâng cao: `--series` (bộ truyện nhiều file), `--genre` (override thể loại), `--images N` `--videos M` (override số lượng), `--force-redo` (chạy lại từ đầu)
  6. Cách paste output vào AI tools:
     - Gemini (image): mở https://gemini.google.com → New chat → paste 1 block từ `_image_prompts.txt` → đợi 4K
     - Qwen-Image: tương tự
     - ChatGPT (image): paste vào Image tab
     - Veo3 (video): mở Veo3 trong Antigravity → paste 1 block từ `_video_prompts.txt`
     - Seedance: tương tự
  7. Workflow đề xuất: 10-15 ảnh + 5-7 video cho 1h audio; 20-30 ảnh + 10-13 video cho 2h audio (cite YouTube algorithm rationale ngắn gọn)
  8. Bộ truyện nhiều file (Series): explain `--series <name>` + character-bible.md tự động lưu ở `~/.gemini/bibles/`
  9. Troubleshooting: top 5 lỗi thật từ Phase 5 + cách khắc phục
  10. FAQ: 5-7 câu hỏi thường gặp (đam mỹ có hỗ trợ không? truyện Tây không? thay đổi prompt được không? làm sao backup bible?)
- `antigravity/README.md` — 50-line note: link tới HUONG-DAN-SU-DUNG.md + Antigravity-specific Windows symlink caveat
- `README.md` — REWRITE from Phase 1 skeleton:
  - Title + 1-line tagline VN
  - Demo screenshot/gif slot
  - Quick install (1 command Linux/Mac, link to Windows)
  - Quick usage (1 example command)
  - Full guide link → `HUONG-DAN-SU-DUNG.md`
  - License + credit

### Modify
- `README.md` from Phase 1 (was 30-line skeleton)

### Delete
- (none)

## Implementation Steps

1. **Outline HUONG-DAN-SU-DUNG.md** with 10 section headers (above); collect Phase 5 issues for §9 troubleshooting
2. **Write §1-4** (overview + install + basic usage) — straightforward; reuse install commands from Phase 1 INSTALL.md
3. **Write §5** (advanced flags) — 1 worked example per flag
4. **Write §6** (paste-to-AI) — most important section for user; include exact URL + UI step description per tool; note that Veo3 inside Antigravity uses different paste flow than web Gemini
5. **Write §7** (workflow đề xuất) — table: audio duration → images + videos count + rationale (1 line cite YouTube algorithm)
6. **Write §8** (series workflow) — explain bible mechanic in plain VN; show 2-file example
7. **Write §9** (troubleshooting) — list top 5 from Phase 5 test logs; each entry: symptom → diagnose → fix
8. **Write §10** (FAQ) — including explicit đam mỹ refusal explanation + how to extend to new genres (point to references/genre-keywords.md)
9. **Rewrite README.md** — replace Phase 1 skeleton with expanded version; keep skimmable
10. **Write antigravity/README.md** — short Windows caveat + link forward
11. **Add docs/img/ directory** (empty, with .gitkeep) — for future screenshots
12. **Final pass**: cross-link all 3 docs; verify all commands run as documented; spell-check VN

## Todo List

- [ ] `HUONG-DAN-SU-DUNG.md` written (10 sections, ≤500 lines)
- [ ] `README.md` expanded from skeleton (≤150 lines)
- [ ] `antigravity/README.md` written (50 lines)
- [ ] `docs/img/.gitkeep` placeholder created
- [ ] Cross-links between 3 docs verified
- [ ] All commands in docs tested by running them fresh
- [ ] VN spell-check pass

## Success Criteria

- [ ] A non-developer VN user can install + run + paste outputs to Gemini/Veo3 using only `HUONG-DAN-SU-DUNG.md`
- [ ] Troubleshooting section addresses ≥5 real issues from Phase 5
- [ ] README.md fits on one GitHub screen without scrolling past quickstart
- [ ] đam mỹ refusal explicitly documented in FAQ
- [ ] Cross-file series workflow has explicit step-by-step example
- [ ] All paste-to-AI instructions tested manually (open each tool, follow doc, confirm works)

## Risk Assessment

| Risk | Mitigation |
|---|---|
| Veo3 UI changes break paste instructions | Note doc date; recommend user re-check official Veo3 docs if UI differs |
| Vietnamese phrasing too technical for target user | Re-read as a YouTube creator (not developer) before publish; rewrite jargon |
| Troubleshooting section becomes stale | Reference Phase 5 test log dates; flag for review every 3 months |
| docs/img/ stays empty (no screenshots ever added) | Acceptable — skill is text-output focused; screenshots are nice-to-have |
| FAQ misses common question | Add "missing FAQ → open GitHub issue" footer |

## Security Considerations

- No secrets, no credentials in docs
- Bible backup instruction (FAQ): show `cp ~/.gemini/bibles/* ~/backup/` — user-local only, no cloud sync recommended (privacy)

## Next Steps

- **Unlocks:** v1.0.0 release tag
- **Post-release:** `/ck:journal` entry; portfolio add; gather user feedback for v2 (reference image pattern deferred from v1)
