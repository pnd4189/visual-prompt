# Brainstorm — Visual Prompt Skill for Antigravity CLI

**Date:** 2026-05-22 22:30
**Status:** Approved — ready for `/ck:plan`
**Skill name:** `/visual-prompt`
**Target platform:** Antigravity CLI (Google) — active Gemini Ultra agent
**Repo:** `/home/dung/VIBE_CODING/1. OTHERS/visual-prompt`

---

## 1. Problem statement

User làm YouTube audio truyện tiên hiệp / web novel Trung Quốc (1h-2h/file, 8k-18k từ VN). Cần skill standalone đọc file text VN đã proofread → sinh image + video prompts chất lượng 4K, copy-paste vào Gemini / Qwen / ChatGPT (ảnh) + Veo3 / Seadream (video). Prompts phải coherence theo mạch story, character consistency cross-file trong cùng bộ truyện.

## 2. Scope

### IN
- Đọc `.txt` / `.docx` VN (đã proofread, có chapter boundary `Chương N`)
- Auto-extract + persist character bible cross-file trong series folder
- Auto-detect genre (đọc 2-3 chương đầu) + cho phép `--genre` override
- Sinh `_image_prompts.txt` + `_video_prompts.txt` per file
- 2-pass workflow: Scene Plan (toàn file) → Expand từng scene (chi tiết 4K)
- Resume cache scene-level (skip scene đã có)
- Antigravity slash command `/visual-prompt`

### OUT (cố ý)
- KHÔNG proofread / clean text (đã có `chinese-novel-proofreader`)
- KHÔNG TTS export
- KHÔNG thực sự gọi AI image/video generator
- KHÔNG xuất `_universal_prompts.txt` (user xác nhận không cần)
- KHÔNG hỗ trợ raw Chinese text (chỉ VN đã proofread)
- KHÔNG hỗ trợ đam mỹ / ngôn tình specific

## 3. Final design decisions

| Item | Decision | Rationale |
|---|---|---|
| Skill scope | Standalone, không động chinese-novel-proofreader | User confirmed |
| Input format | VN đã proofread, multi-chapter | User confirmed |
| Visual density | 1 ảnh / 90s + 1 video / 10 phút audio | User chose medium density |
| Bible extraction | Auto-extract LLM | User confirmed |
| Bible persistence | Lưu trong input folder (series-level) | User confirmed |
| Platform format | Image: prose 250-350 từ; Video: Veo3 spec (Camera + Beats + Audio) | User confirmed |
| Command + cache | `/visual-prompt` + auto-resume scene cache | User confirmed |
| Genre handling | Auto-detect (đọc 2-3 chương đầu) + `--genre` override | User confirmed |
| Story coherence | 2-pass: Scene Plan → Expand | User confirmed |
| Tech stack | Pure LLM-driven + Python I/O minimal (v3.6 pattern) | User confirmed |
| Antigravity install | Full pattern: extension.json + .toml + setup.sh/.bat | User confirmed |
| Pass 1 chunking | KHÔNG cần — Gemini Ultra quota khủng | User confirmed |
| Bible auto-append nhân vật mới | LLM tự quyết, không cần user confirm | User confirmed |
| Universal prompts file | KHÔNG xuất | User confirmed |

## 4. Architecture

```
/visual-prompt <input.txt> [--series <name>] [--genre <name>] [--images N] [--videos M] [--force-redo]
                       │
                       ▼
   Step 1 — load_input.py: .txt/.docx → JSON chapters list
                       │
                       ▼
   Step 2 — Bible (LLM):
     - Check {input_dir}/character-bible.md
     - Exists → load + LLM augment (append nhân vật mới tự động)
     - No → extract từ chương 1-2
     - Save atomic
                       │
                       ▼
   Step 3 — Genre detect (LLM, 1 turn):
     - Read 2-3 chương đầu
     - Pick: tienxia | wuxia | xuanhuan | urban-cultivation | historical | gamelit | horror | fantasy
     - Pull style anchor + genre keywords từ references/genre-keywords.md
     - Override via --genre
                       │
                       ▼
   Step 4 — Scene Plan (Pass 1, LLM, 1 turn cho cả file):
     - Read FULL text + bible
     - Auto-calculate count: images = round(wordcount/200), videos = round(images/7)
     - Override via --images / --videos
     - Output .work/scene-plan.md:
         Scene 001 (establishing) | chapter 1 | "Hàn Lập sáng sớm bản làng" | image
         Scene 002 (action)       | chapter 1 | "đạp trúc kú cây ngã"      | image
         ...
         Video 001 (action)       | chapter 3 | "đột phá luyện khí kỳ"     | video
                       │
                       ▼
   Step 5 — Expand (Pass 2, LLM, sequential per scene):
     - For each scene in plan (skip nếu .work/scene-NNN.md đã có):
       - Read scene context (paragraph range trong text)
       - Paste Identity Anchor verbatim từ bible
       - Apply prompts/prompt-expander-{image|video}.md
       - Image: prose 250-350 từ, 3-layer composition, anti-drift
       - Video: Camera + 3 Action Beats + Audio Cue, ≤ 800 từ
       - Self-check uniqueness vs scene trước (>70% khác)
       - Write .work/scene-NNN.md atomic
                       │
                       ▼
   Step 6 — Assemble (assemble_outputs.py):
     - Concat .work/scene-NNN.md → 2 files
     - Filter type=image → _image_prompts.txt
     - Filter type=video → _video_prompts.txt
     - Print summary JSON
```

## 5. File layout

```
visual-prompt/
├── SKILL.md                                # Entry context (Antigravity reads)
├── gemini-extension.json                   # Declares skill cho Antigravity
├── README.md                               # Quick start VN
├── HUONG-DAN-SU-DUNG.md                    # User guide
├── setup.sh / setup.bat                    # 1-shot installer (symlink)
├── commands/
│   └── visual-prompt.toml                  # Slash command + 6-step workflow
├── scripts/
│   ├── load_input.py                       # .txt/.docx → JSON chapters
│   ├── assemble_outputs.py                 # concat .work → 2 files
│   ├── calc_scene_count.py                 # wordcount → image/video count
│   └── _io_utils.py                        # atomic write
├── prompts/
│   ├── bible-extractor.md                  # Step 2
│   ├── bible-augmenter.md                  # Step 2 (cross-file mode)
│   ├── genre-detector.md                   # Step 3
│   ├── scene-planner.md                    # Step 4 (Pass 1)
│   ├── prompt-expander-image.md            # Step 5 image
│   └── prompt-expander-video.md            # Step 5 video (Veo3)
├── references/
│   ├── visual-prompt-template.md           # COPY từ proofread skill + enhance
│   ├── genre-keywords.md                   # VN↔EN cho 7 genres
│   ├── identity-anchor-rules.md            # Cross-file consistency
│   └── youtube-pacing-guide.md             # Khuyến nghị image/video count
├── antigravity/
│   ├── INSTALL.md                          # symlink guide Linux/Mac/Win
│   └── README.md                           # quick reference
└── plans/
    └── reports/
        └── brainstorm-260522-2230-visual-prompt-skill.md   # File này
```

## 6. Output per run

Input: `Bo-Tu-Tien/tap-01.txt` (10k từ ≈ 1h15min audio)

```
Bo-Tu-Tien/
├── tap-01.txt
├── character-bible.md                    # ← Series-level, auto-update mỗi file
└── tap-01_visuals/
    ├── tap-01_image_prompts.txt          # ~50 image prompts prose
    ├── tap-01_video_prompts.txt          # ~7 video prompts Veo3 spec
    ├── tap-01_scene-plan.md              # Pass 1 output (reference / debug)
    └── .work/                            # Resumable cache
        ├── scene-001.md ... scene-057.md
        └── ...
```

## 7. Scene count formula

```python
def calc_scene_count(wordcount: int, override_images=None, override_videos=None):
    if override_images: images = override_images
    else: images = max(5, round(wordcount / 200))      # ~1 ảnh / 90s audio @ 140wpm
    if override_videos: videos = override_videos
    else: videos = max(2, min(30, round(images / 7)))  # ~1 video / 10min, capped
    return images, videos
```

| Wordcount VN | Audio (≈140 wpm) | Images | Videos |
|---|---|---|---|
| 2,000 | 15min | 10 (floored) | 2 (floored) |
| 8,000 | 1h | 40 | 6 |
| 12,000 | 1h25 | 60 | 9 |
| 16,000 | 2h | 80 | 11 |
| 25,000 | 3h | 125 | 18 |

Override: `--images 30 --videos 5` hoặc `--ratio dense|normal|sparse`

## 8. Prompt format spec

### Image prompt (Gemini / Qwen / ChatGPT / Imagen — prose 250-350 từ)

```
[Scene NNN — <tag> — "<≤8-word title VN>"]

<prose 250-350 từ chứa đầy đủ:>
- Style anchor (Chinese xianxia ink painting / Guofeng / wuxia cinematic / …)
- Setting: location + time + weather + season (cụ thể, không generic)
- Foreground: prop / texture gần camera
- Midground: <Identity Anchor verbatim từ bible> + pose + action + expression
- Background: depth marker + atmospheric perspective
- Lighting: source + direction + quality
- Mood: 2-3 adjective từ vocabulary
- Color palette: 3-5 màu cụ thể
- Composition note (rule of thirds / scale contrast / depth)

Avoid: <anti-drift list: Western fantasy castles, blonde Caucasian, modern clothing,
gothic spires, cartoon, deformed hands>
```

### Video prompt (Veo3 / Seadream — spec format, ≤ 800 từ)

```
[Scene NNN — duration: 8s — <tag>]

Camera: <shot type + lens + movement>
Action Beat 1 (0-3s): <verb + object + reaction>
Action Beat 2 (3-6s): <verb + object + reaction>
Action Beat 3 (6-8s): <verb + object + reaction>
Setting: <location + atmospheric layer + time>
Atmosphere: <2-3 atmosphere words>
Lighting: <source + direction + mood>
Style: Cinematic xianxia, <pace note>, <reference film optional>
Audio Cue: <ambient + cue at specific timestamps>
Tech: 16:9, 24fps cinematic, DoF note, motion blur note
Negative: <anti-drift>
```

## 9. Quality bar (acceptance criteria)

- [ ] `character-bible.md` save thành công, có ≥1 main character với Identity Anchor block verbatim
- [ ] Scene plan có đúng số scenes theo formula (hoặc theo `--images`/`--videos`)
- [ ] Mỗi image prompt 250-350 từ, có Identity Anchor + 3-layer composition + negative
- [ ] Mỗi video prompt có Camera + 3 Action Beats timestamp + Audio Cue + ≤ 800 từ
- [ ] Uniqueness ≥ 70% giữa scenes gần nhau (LLM self-check Pass 2)
- [ ] Không có Western tropes (anti-drift)
- [ ] File 2 cùng series load được bible file 1, main character xuất hiện cùng Identity Anchor verbatim
- [ ] Resume hoạt động: re-run cùng input → skip scenes đã có trong `.work/`
- [ ] `setup.sh` cài thành công trên Linux/Mac → `/visual-prompt` autocomplete trong Antigravity

## 10. Risks & mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Genre detect sai khi chương 1 là flashback | Med | Đọc 2-3 chương đầu thay vì 1 |
| Bible drift cross-file | Med | Identity Anchor verbatim rule, save full appearance block, augment-only mode |
| LLM lặp scene gần nhau | High | Pass 2 self-check uniqueness, regenerate nếu >80% overlap |
| Veo3 truncate prompt dài | Low | Cap ≤ 800 từ, 3 action beats only |
| File rất ngắn (<2k từ) | Low | Floor 5 images + 2 videos, không apply formula |
| Antigravity setup phức tạp Windows | Med | setup.bat + copy fallback trong INSTALL.md |
| Pass 1 plan output token cao | Low | Gemini Ultra OK (user confirmed quota khủng) |

## 11. Implementation phases (preview cho `/ck:plan`)

1. **Phase 1 — Skeleton & install** — SKILL.md, gemini-extension.json, commands/visual-prompt.toml, setup.sh/.bat, INSTALL.md
2. **Phase 2 — Python I/O scripts** — load_input.py, calc_scene_count.py, assemble_outputs.py, _io_utils.py
3. **Phase 3 — Reference docs** — copy + enhance visual-prompt-template.md, genre-keywords.md, identity-anchor-rules.md, youtube-pacing-guide.md
4. **Phase 4 — Prompt files** — bible-extractor.md, bible-augmenter.md, genre-detector.md, scene-planner.md, prompt-expander-image.md, prompt-expander-video.md
5. **Phase 5 — End-to-end test** — chạy thử trên 1 file truyện ngắn (~2k từ) + 1 file dài (~10k từ), verify output + bible cross-file
6. **Phase 6 — Docs + README** — HUONG-DAN-SU-DUNG.md với ví dụ thực tế

## 12. Next steps

- User approve design → invoke `/ck:plan` với file này làm context
- `/ck:plan` mode: default (đây là greenfield, không có code cũ để bảo vệ qua TDD)

---

## Appendix A — Tham khảo từ codebase

- **`chinese-novel-proofreader/references/visual-prompt-template.md`** (14KB) — copy gốc + enhance:
  - Genre Keywords VN↔EN cho tiên hiệp/võ hiệp/luyện đan/settings/characters
  - 7 Scene Tags (establishing/action/dialogue/reveal/emotional/ritual/travel)
  - Per-Platform Tweaks table (Midjourney/Flux/Imagen/Nano Banana/Veo3/Sora/Kling)
  - Anti-Drift Guard List (10 Western tropes cần tránh)
  - Identity Anchor format
- **`chinese-novel-proofreader/prompts/visual-guideline.md`** — pattern free-form prompt cho LLM agent
- **`chinese-novel-proofreader/scripts/load_input.py`** — chapter regex + .txt/.docx loader (reuse trực tiếp)
- **`chinese-novel-proofreader/scripts/assemble_outputs.py`** — pattern parse `.work/` + atomic write 3 files (adapt cho 2 files)
- **`chinese-novel-proofreader/commands/proofread.toml`** — pattern slash command 6-step workflow trong TOML
- **`chinese-novel-proofreader/antigravity/INSTALL.md`** — symlink guide cross-platform
- **`Prompt_generator/.claude-skill/coloring-prompt/`** — pattern 3-subagent architecture + config.json

## Appendix B — Câu hỏi đã clarify

1. Genre detect đọc 2-3 chương đầu ✓
2. Không cần fallback chunk Pass 1 — Gemini Ultra quota khủng ✓
3. LLM tự append nhân vật mới vào bible không cần user confirm ✓
4. Không xuất `_universal_prompts.txt` ✓
