# Red-Team Review — visual-prompt skill plan

**Reviewer role:** adversarial / hostile.
**Plan:** `plans/260522-2230-visual-prompt-skill-implementation/`
**Date:** 2026-05-22
**Verdict:** plan is solid in concept but ships with 6 critical workflow gaps that will break first real run.

---

## Findings

### 1. assemble_outputs.py "verbatim copy" claim is false — schema mismatch with Phase 4

**SEVERITY:** critical
**LOCATION:** phase-02 §Related Code Files; phase-04 architecture diagram
**RISK:** plan.md and phase-02 both say `assemble_outputs.py` is "ADAPTED from proofreader". Reading the actual proofreader script (`chinese-novel-proofreader/scripts/assemble_outputs.py:32-70`) reveals its parser expects:
  - input filenames `chapter-NNN-prompts.md` (regex `_CHAPTER_NUM_RE`)
  - section structure `## Scene N — tag` followed by `### Image` and `### Video` subheaders
  - 6 output files including `_proofread.txt`, `_vieneu.txt`, `_gwen.txt`, `_universal_prompts.txt`
  - mandatory `chapter-*-clean.txt` files (raises `RuntimeError` if absent — see line 80-81)
  - hard-coded TTS imports (`format_for_vieneu`, `format_for_gwen` — line 30)

Phase 4 writes `.work/scene-NNN.md` with `## Image Prompt` / `## Video Prompt` headers (not Scene blocks). The "adapt" is actually a near-rewrite, plus the new format breaks resume cache assumptions (no chapter ID in filename).

Worse: phase-02 success criterion says "Wrote N image prompts + M video prompts" — that's a different pipeline than proofreader assembler. LOC estimate "120 lines adapted" is plausible only if the import dependency on `format_tts.py` is severed, the scene-block regex is fully rewritten, and the missing-clean-files error path is removed.

**RECOMMENDATION:** Rename phase-02 task from "ADAPT" to "REWRITE (inspired by proofreader)". Explicitly list deletions: no TTS imports, no clean-files requirement, no universal_prompts output, no work-dir cleanup. Specify the NEW regex for `scene-NNN.md` files. Add success criterion: `assemble_outputs.py` has zero imports from `format_tts`, `_tts_*`, `text_normalizer`.

---

### 2. Resume cache cannot survive scene-plan changes — stale cache silently produces wrong output

**SEVERITY:** critical
**LOCATION:** phase-04 §Implementation Steps 9; phase-05 §Test 05
**RISK:** Resume logic checks `if .work/scene-NNN.md exists: skip`. But scene IDs come from `.work/scene-plan.md`, which is regenerated on every non-`--force-redo` run. If user edits input file (adds a chapter, fixes a typo that shifts wordcount), Pass 1 produces a different scene plan but Pass 2 reuses old `scene-001.md` — old `scene-001` may now reference deleted/different content. No checksum links scene file to scene-plan row.

Same risk: bible augmentation between runs adds a new character → scene-plan now flags scene-001 as having Character X, but cached scene-001.md was written before that character existed. Output is internally inconsistent.

**RECOMMENDATION:** Either (a) write `.work/scene-plan.lock` with content-hash of scene-plan + input wordcount; invalidate ALL cached scenes if hash changes, OR (b) embed scene-plan-row hash in each scene-NNN.md frontmatter and skip-cache only if hash matches. Document the choice in phase-04. Phase-05 Test 05 currently tests Ctrl+C resume; add a 2nd resume test: edit input between runs → verify cache invalidates.

---

### 3. Two scenes share one file (scene-NNN.md) — image-only vs image+video scenes collide

**SEVERITY:** critical
**LOCATION:** phase-04 §Architecture workflow Step 6 "for each scene"; phase-02 assemble_outputs.py spec
**RISK:** Plan numbers scenes from 1..N where N = total images. But only M ≤ N scenes carry video (M ≈ N/7). The workflow says for video scenes, "append video block" to the same `scene-NNN.md`. assemble_outputs scans `.work/scene-*.md`, extracts `## Image Prompt` block AND `## Video Prompt` block (if present).

Problem: scene-plan flags `flag_for_video: true` for ~M scenes. Phase 5 success criterion says "5 images, 1 video output" for override. But you wrote N=10 image scenes and only 2 of them have video — so 8 scene files have only image, 2 have both. assemble_outputs.py spec says "concatenate all video prompts" — what about the 8 scenes with no video block? Per phase-02 risk row: "malformed (missing `## Image Prompt`) → logs WARNING + skips". WARNING per scene = 8 warnings on a 50-scene file = log noise that hides real errors.

Worse, the numbering is confusing for the user: `--- SCENE 1 ---`, `--- SCENE 2 ---` in `_video_prompts.txt` won't even be sequential — could be 1, 7, 14, 21, 28, 35, 42, 49 — looking like missing data.

**RECOMMENDATION:** Decide ownership: either (a) split into two separate filename schemes (`.work/img-NNN.md` + `.work/vid-NNN.md` with independent indexes), OR (b) keep scene-NNN.md but renumber the video output with its OWN sequential index (Video 1, 2, 3...) in `_video_prompts.txt` and use cross-ref `[Video 3 → from Scene 21]`. Document the choice in phase-02 + phase-04 BEFORE coding the assembler.

---

### 4. Wall-time budgets (3/12/25 min) are wishful thinking given LLM latency

**SEVERITY:** high
**LOCATION:** phase-05 §Non-functional + Success Criteria
**RISK:** Medium file (9k words) = ~45 image scenes + ~6 video scenes = 51 LLM calls minimum for Pass 2. Plus 1 bible call + 1 genre call + 1 scene-plan call = 54 LLM calls. Gemini Ultra typical latency: 8-25 s per moderate-complexity response (200-300 word output). Even at optimistic 10s/call: 540s = 9 min just for Pass 2. Add Pass 1 (scene-plan with full chapters loaded — can be 30-90s), bible extraction, scene-plan uniqueness self-check which may force re-gen of duplicates → realistic medium-file time is 15-25 min, not <12 min.

Long file (18k words, 90 images + 13 videos = 103 calls × 10s = 17 min just Pass 2) → realistic 30-45 min, not <25 min.

Short file (2k words clamped to 5 images + 2 videos = ~7 calls + setup) probably IS <3 min. Only the smallest budget is realistic.

**RECOMMENDATION:** Either widen budgets to 5/25/45 min, or design batching: scene-planner can emit a 5-scene batch per LLM turn (5 scenes × 200 words = 1000 words output, fits in 1 turn). Drops 45 calls → ~9 calls for medium. This is a real architectural decision not a budget tweak. Confirm with user before coding.

---

### 5. Antigravity slash-command does NOT support flag parsing — `--series`, `--genre`, `--images`, `--videos`, `--force-redo` will not work as designed

**SEVERITY:** critical
**LOCATION:** plan.md architecture line; phase-04 step 8-9; phase-05 Test 06
**RISK:** Antigravity slash commands receive arguments via `{{args}}` template substitution as a SINGLE STRING — no argv parsing happens at command boundary. Proven by the proofreader pattern: `proofread-cn.toml` includes a fragment "Parse arguments as follows" inside the LLM prompt, then asks the LLM to parse argv-like flags by string-matching. This means:
  - Flag parsing reliability = LLM disobedience floor (~95%, not 100%)
  - `--images 5` vs `--images=5` vs `-i 5` — LLM may handle inconsistently across runs
  - Numeric typed flags can be misread (e.g., LLM treats "5" as string, passes to script)
  - No validation: invalid flag like `--imgs 5` will be silently ignored by LLM (not "Unknown flag: --imgs" error)

Plan-claimed success criterion `/visual-prompt short-sample.txt --images 5 --videos 1 → exactly 5 images, 1 video` is unverifiable without explicit LLM-parse logic in the .toml prompt body. Phase-04 step 8-9 talk about "wire flag" with zero detail.

**RECOMMENDATION:** Add explicit "Argument Parsing" section to `commands/visual-prompt.toml` (mirror proofreader pattern lines 11-23): enumerate each flag, exact syntax accepted, default value, behavior on unknown flag. Add to phase-04 success criterion: "Unknown flag (e.g. `--imgs`) triggers error message in Vietnamese — does NOT silently drop." Phase-05 Test 06 must include negative-test: bad flag input.

---

### 6. Verbatim Identity Anchor enforcement has no detection mechanism in the loop

**SEVERITY:** high
**LOCATION:** phase-04 risk row; phase-05 Quality Bar
**RISK:** Plan says "LLM ignores verbatim rule → mitigate via 2 bad/good examples in prompt + Phase 5 acceptance test checks character description string match across scenes". The "acceptance test" is manual eyeball, not automated. There is no per-scene self-check that confirms the Subject section contains the bible's Identity Anchor block byte-for-byte. Once the user runs this on file 50 in a series, drift is inevitable, and the manual check is impractical.

This is the design's biggest empirical claim (R2 verbatim 8.5/10 vs paraphrase 5-6/10). If the implementation can't guarantee it, the validated quality benefit disappears.

**RECOMMENDATION:** Add a tiny verifier script `scripts/check_anchor.py` that takes `character-bible.md` + `_image_prompts.txt` and reports per scene: anchor block present (yes/no), substring distance from canonical. Wire into `assemble_outputs.py` post-write step; emit `_anchor_audit.md` warning sidecar. This is +30 LOC, prevents silent drift, makes the headline quality claim falsifiable.

---

### 7. Vietnamese filename with diacritics + spaces will break in shell-quoted args

**SEVERITY:** high
**LOCATION:** phase-01 risk "Repo path has spaces"; phase-02 risk Vietnamese filename
**RISK:** Plan acknowledges both risks but mitigates only with "use pathlib.Path" + "quote `$(pwd)`". This is insufficient for the actual workflow path:
  1. `commands/visual-prompt.toml` `{{args}}` substitution may NOT auto-quote — if user types `/visual-prompt /home/dung/Truyện Tu Tiên/Phàm Nhân.txt`, the LLM-generated shell command may become `python3 scripts/load_input.py /home/dung/Truyện Tu Tiên/Phàm Nhân.txt` (3 args), bash splits on space.
  2. Output filename `<input-stem>_image_prompts.txt` — if stem is `Phàm Nhân`, this hits NFC vs NFD normalization issues on macOS (HFS+ stores NFD, Python gets NFD back, comparison with NFC input string fails silently).
  3. Bible path `~/.gemini/bibles/<series>.md` — if `--series Tru Tiên` with spaces and diacritic, same problems.
  4. The actual working dir contains `1. OTHERS` with a space and a dot — Antigravity `{{args}}` may not handle `.` in absolute paths consistently.

**RECOMMENDATION:** Mandate in phase-04 toml: every shell command must wrap user-derived paths in double-quotes (`"{path}"`). Add phase-02 success criterion: load_input.py succeeds on `/tmp/Truyện Tu Tiên - Chương 1.txt` (with space + diacritic + dash). Add phase-05 Test 07: fixture with diacritic-heavy filename + `--series Tru Tiên`. Document NFC normalization expectation (Python defaults to NFC string compare, but file paths from os.listdir may be NFD on Mac).

---

### 8. Reuse claim "3 scripts verbatim" is inaccurate — assemble_outputs needs heavy rewrite (see #1)

**SEVERITY:** medium
**LOCATION:** plan.md §Dependencies "Codebase reuse"
**RISK:** Plan says 3 scripts copied verbatim. Reality (verified):
  - `load_input.py` (73 lines): can be verbatim ✓ — chapter regex already matches Vietnamese (`Chương|CHƯƠNG`), encoding fallback present
  - `_io_utils.py` (50 lines): can be verbatim ✓
  - `assemble_outputs.py` (153 lines): CANNOT be verbatim (see Finding #1)

The "~250 LOC total" estimate is also off: load_input (73) + _io_utils (50) + calc_scene_count (~60 new) + assemble rewrite (~120) = ~303 LOC, plus `__init__.py`. Not catastrophic but creates a 20% schedule slip on phase 2 if "verbatim" implies "no review".

**RECOMMENDATION:** Update plan.md dependencies row: "2 scripts verbatim (load_input, _io_utils); 2 scripts new (calc_scene_count, assemble_outputs rewrite). ~300 LOC total." Reset phase-02 effort estimate from 0.5d to 0.75d.

---

### 9. Setup.bat "non-admin copy fallback" is silently broken for symlink-only workflows

**SEVERITY:** medium
**LOCATION:** phase-01 step 7; INSTALL.md spec
**RISK:** Copy fallback breaks the entire iterate-edit-test loop on Windows. User edits `prompts/scene-planner.md` in repo → copy at `~/.gemini/.../skills/visual-prompt/prompts/scene-planner.md` is stale → Antigravity reads stale prompt → user thinks edit didn't work, wastes hours. Proofreader's INSTALL.md does note "không tự đồng bộ — copy lại thủ công" but it's a one-line warning easy to miss.

Also affects developer testing during Phases 4-5: every prompt iteration requires re-copy. Phase 5 will hit this hard.

**RECOMMENDATION:** Either (a) require Developer Mode on Windows 10/11 (Settings → For Developers → Developer Mode = ON, then `New-Item -ItemType SymbolicLink` works without admin), document this prominently, OR (b) provide a `sync.bat` script users run after each edit. Phase-01 INSTALL.md should call this out in bold near the copy-fallback section, not at the bottom.

---

### 10. Genre detector "sample first + middle + last chapter" breaks on single-chapter files

**SEVERITY:** medium
**LOCATION:** phase-04 §genre-detector.md spec; phase-02 load_input fallback
**RISK:** load_input.py line 40-41: if no `Chương` regex match, returns 1 chapter "Chương 1" with the whole text. Genre detector then has 1 chapter to "sample first+middle+last" — all the same chapter, no flashback-avoidance benefit. Also for short files (2k words = 1-2 chapters), first+middle+last is functionally same as "all".

For long single-file novels with no chapter markers (a real edge case — user pastes raw text), detector sees 1 monolithic chapter and may misclassify based on opening prose.

**RECOMMENDATION:** In `prompts/genre-detector.md`, add chapter-count branch: if K=1, slice text into 3 equal segments (first 1/3, middle 1/3, last 1/3) and sample those. If K=2, use chapter 1 + chapter 2 only. Document in phase-04 spec.

---

### 11. Bible-augmenter "byte-identical existing rows" claim is unenforceable from LLM-only

**SEVERITY:** high
**LOCATION:** phase-04 §bible-augmenter.md; phase-05 Test 04 success criterion "diff = 0"
**RISK:** Plan instructs LLM "PRESERVE EXISTING ROWS VERBATIM — append-only". LLMs systematically reflow whitespace, fix typos in pre-existing text, normalize punctuation, change `—` to `--`. Test 04 says verify `bible existing rows byte-identical (diff = 0)` — this will fail on first run. No mitigation script.

The proofreader uses LLM-only too, but its character bible is regenerated per-file (no cross-file expectation). visual-prompt is the FIRST skill claiming cross-file persistence, and the LLM cannot be trusted to honor byte-identical preservation.

**RECOMMENDATION:** Add `scripts/append_bible_row.py`: takes existing bible + JSON of new rows → appends only, never touches existing bytes. Bible-augmenter.md LLM step outputs ONLY the new rows as JSON; script appends them. This gives byte-identity by construction, not by hope.

---

### 12. đam mỹ block enforcement is keyword-based — trivially bypassable

**SEVERITY:** medium
**LOCATION:** phase-03 references/genre-keywords.md; phase-04 genre-detector.md
**RISK:** Block depends on detecting đam mỹ keywords in 3 sample chapters. User can rename "Hắc Hoàng Tử" to "Hắc Hoàng Nữ" pronouns or use ambiguous opening chapters → bypass. Per user-confirmed decision (đam mỹ BLOCKED), the safety net is single-layer and easily fooled.

This is the user's explicit policy decision — implementation cannot make it bulletproof, but should be honest about limits.

**RECOMMENDATION:** Document explicit scope of the block: "best-effort keyword filter on first 3 chapters; not a content moderation system". Add to phase-06 FAQ: "Skill detects đam mỹ via vocabulary — if your file uses ambiguous opening chapters, it may proceed. Output quality not guaranteed for these cases." Do NOT escalate to multi-layer LLM moderation (out of scope, YAGNI per user). Just be honest.

---

### 13. SKILL.md ≤200 lines budget is contradicted by 6-step workflow + spec links

**SEVERITY:** low
**LOCATION:** phase-01 non-functional req
**RISK:** Proofreader SKILL.md (verified) = 116 lines for a 6-step workflow + 13 scripts. visual-prompt has 6 steps + 4 scripts + 6 references + 6 prompts + flag handling + đam mỹ refusal + series workflow + format spec teasers. Plausibly fits in 200 if terse, but tight. The risk is mid-implementation creep: "just add a paragraph for X" → 250 lines → Antigravity truncates → silent quality drop.

**RECOMMENDATION:** Add a hard line-count CI check in phase-05: `wc -l SKILL.md` ≤200, fail-build if exceeded. Trim by linking to references rather than duplicating spec.

---

### 14. References/ load strategy "each <300 lines, load only relevant per step" is unaudited

**SEVERITY:** medium
**LOCATION:** phase-03 risk row; phase-04 prompt files
**RISK:** Phase 3 caps each reference <300 lines. Phase 4 prompts say `prompt-expander-image.md` loads `@references/visual-prompt-template.md + scene-tag-camera-mapping.md + negative-lists.md` (3 refs × 300 = 900 lines), plus the prompt file itself (~180 lines), plus scene-plan row, plus bible (could be 50-200 lines for 20-char series), plus relevant chapter excerpt (could be 2000 words = ~500 lines). That's ~2000+ lines of context per image-prompt call, 45 times for a medium file.

Total context per medium-file run: ~100k tokens just on prompt context alone. Gemini Ultra 1M context fits, but cost/latency multiplier is real (see Finding #4).

**RECOMMENDATION:** Add to phase-03 success criteria: measure actual token count of "max context per prompt-expander call" and document it in plan.md. If >50k tokens, consider trimming references or caching them once per workflow run (Gemini context caching API if available).

---

### 15. Test fixtures plan to "borrow xianxia excerpts" — copyright risk + reproducibility risk

**SEVERITY:** low
**LOCATION:** phase-05 §Implementation Step 1; security row
**RISK:** Plan says "source from existing proofreader test data if available; else write/borrow 3 short xianxia excerpts". "Borrow" from where? Real published novels = copyright issue if committed. "Existing proofreader test data" = need to verify what's actually there (may or may not exist). Plan defers this to phase-05 with no fallback.

**RECOMMENDATION:** Before phase-05 starts, generate 100% synthetic test fixtures using Gemini itself: prompt "write a 2000-word xianxia chapter pastiche in Vietnamese, mention tu tiên + đột phá + thiên kiếp, original characters". Commit those to `plans/test-fixtures/`. Phase-05 risk row already says "synthesize" — make it the default, not the fallback.

---

### 16. `.work/` resume cache has no version stamp — code changes invalidate cache silently

**SEVERITY:** medium
**LOCATION:** phase-04 resume logic
**RISK:** User runs v0.1.0 → produces `.work/scene-001.md`. Skill updated to v0.2.0 (image format changed from 200-300w to 250-350w). User reruns same input without `--force-redo` → cached scene-001.md is reused (old format) → final output has mixed formats across scenes. No version check.

**RECOMMENDATION:** Embed `skill_version: 0.1.0` in scene-NNN.md frontmatter. Resume check: only skip if `frontmatter.skill_version == current_skill_version`. Add to phase-04 spec; +5 LOC effort.

---

### 17. `--genre` override doesn't say what happens to genre-detector confidence

**SEVERITY:** low
**LOCATION:** phase-04 step 8; phase-05 Test 06
**RISK:** If user passes `--genre vo-hiep` but detector finds clear xianxia evidence (confidence 0.95), does the override silently win? Or does it ask "are you sure?" Or does it abort? Plan is silent. Bad UX risk: user fat-fingers `--genre dam-my` for a legitimate xianxia novel → đam mỹ refusal fires → user confused.

**RECOMMENDATION:** Phase-04 spec for `--genre`: explicit override always wins (no confirmation). Exception: `--genre dam-my` or `--genre ngon-tinh` is rejected with error "đam mỹ/ngôn tình not supported, regardless of override". Document in phase-06 docs.

---

### 18. python-docx is a runtime dep with native build chains on some platforms

**SEVERITY:** low
**LOCATION:** phase-02 dependencies; phase-01 setup.sh
**RISK:** `python-docx` pure-Python, no native deps — verified. BUT `lxml` (its transitive dep) needs `libxml2-dev` + `libxslt-dev` on Linux. Pip wheel usually works, but on ARM Linux / older distros, pip falls back to source build → fails without system packages. Setup.sh has no Python install at all (per phase-01 spec — Phase 1 only creates symlinks).

**RECOMMENDATION:** Phase-01 setup.sh should `pip install --user python-docx` with try/except → if fail, print "Optional: install python-docx for .docx support: `sudo apt install libxml2-dev libxslt-dev && pip install python-docx`". Don't make `.docx` support a hard dep; .txt-only path should always work.

---

### 19. `calc_scene_count.py` formula `images = round(wc/200)` may produce zero on tiny inputs

**SEVERITY:** low
**LOCATION:** phase-02 step 3
**RISK:** Clamp `images >= 5, videos >= 2`. But for a 500-word file (test of broken input), 500/200=2.5 → round=3 → clamped to 5. So 500-word input → 5 image prompts, each generated from a tiny chapter slice. Outputs will be repetitive or hallucinated.

**RECOMMENDATION:** Add upper guard: if `wc < 1000`, refuse with message "File too short (< 1000 words). Provide a proper chapter or use --force to override." Add to phase-02 success criteria.

---

### 20. Wordcount formula uses `len(text.split())` — Vietnamese has multi-syllable "words" with spaces

**SEVERITY:** low
**LOCATION:** phase-02 step 3; brainstorm §7 (implicit)
**RISK:** `"tu tiên".split() = ["tu", "tiên"]` → 2 tokens. Vietnamese xianxia: "tu tiên đột phá thiên kiếp" = 5 whitespace tokens but ~3 semantic words. Image count formula was probably calibrated against English/Chinese wordcount norms, not Vietnamese tokenization. Could over-shoot image count by 1.3-1.5x.

**RECOMMENDATION:** Either (a) accept the over-shoot (more visuals = OK for YouTube), document the multiplier, OR (b) divide by 1.5 for Vietnamese (target syllable count not word count). Pick one; document in phase-03 youtube-pacing-guide.md.

---

### 21. INSTALL.md proofreader pattern uses `~/.gemini/...` but Antigravity may use different path

**SEVERITY:** medium
**LOCATION:** phase-01 INSTALL.md spec
**RISK:** Plan inherits `~/.gemini/antigravity/skills/` and `~/.gemini/commands/` paths from proofreader. These paths are tied to Gemini CLI v3.6 convention. Antigravity (different IDE — VS Code fork per proofreader docs) may use a different config dir (`~/.antigravity/`, `~/.config/antigravity/`, `$XDG_CONFIG_HOME/antigravity/`). Plan-01 risk row mentions "Antigravity changes context file convention" but not the install-path convention.

**RECOMMENDATION:** Before Phase 1, verify actual Antigravity skill-discovery path (check Antigravity docs or run `ls ~/.gemini ~/.antigravity ~/.config/antigravity 2>/dev/null` after install). Update INSTALL.md to current truth, not inherited assumption.

---

### 22. assemble_outputs scene-plan ordering relies on filename sort; >999 scenes breaks

**SEVERITY:** low
**LOCATION:** phase-02 step 4 "Glob scene-*.md sorted by filename"
**RISK:** Spec says "Glob `.work/scene-*.md` sorted by filename". For NNN format (`scene-001.md`...`scene-999.md`), lexicographic sort = numeric sort. For NNNN (4-digit), no problem. But if calc_scene_count yields >999 (long-long file or override `--images 1500`), and filenames use 3-digit padding, `scene-1000.md` sorts BEFORE `scene-999.md` lexicographically.

**RECOMMENDATION:** Use 4-digit padding everywhere or sort by extracted int (numeric sort, not string). Add success criterion: 1000-scene synthetic test passes. Realistic max is ~100 for 2h audio, so this is low-prio but cheap to get right.

---

### 23. No telemetry / log of LLM call count or token usage — debugging blind

**SEVERITY:** medium
**LOCATION:** plan-wide
**RISK:** When phase-05 timing exceeds budget (likely per #4), there's no log saying "scene-planner took 45s, prompt-expander-image avg 12s × 45 calls = 540s, bible 30s". Without per-step timing, optimization is guessing. Proofreader has `skill_log.py` (opt-in); plan doesn't mention it.

**RECOMMENDATION:** Borrow `skill_log.py` from proofreader (opt-in env var). Add to phase-02 reuse list. Log per workflow step: start/end timestamp + step name. Saves to `.work/run-log.jsonl`. Phase-05 uses this to populate timing claims.

---

### 24. ms-precision timestamps `[00:00-00:02.5]` may not be Veo3-syntax

**SEVERITY:** medium
**LOCATION:** phase-04 prompt-expander-video spec
**RISK:** Plan asserts Google official 5-part formula with ms-timestamps `[00:00-00:02.5]`. R2 research is cited but I cannot verify what Veo3 actually accepts as input. If Veo3 wants `0:00-2.5s`, `00:00:00-00:00:02.500`, or no timestamps at all, output is non-functional. The 250-line video prompt is wrapping unverified Veo3 input format.

**RECOMMENDATION:** Before writing prompt-expander-video.md (phase-04 step 6), make ONE manual test: paste a sample 5-part prompt with `[00:00-00:02.5]` syntax into actual Veo3 → confirm it parses. If syntax differs, update spec BEFORE phase-04 starts. This is a 30-min verification that prevents a full-day rewrite.

---

### 25. No backout / cleanup if workflow fails mid-run

**SEVERITY:** low
**LOCATION:** plan-wide
**RISK:** If phase-04 prompts fail at step 5 (scene-planner returns garbage), there's no rollback. `.work/` accumulates partial scene files, bible may be half-augmented, scene-plan may be stale. Resume next run picks up corrupt state.

**RECOMMENDATION:** Phase-04 commands/visual-prompt.toml top-level: wrap each step in error-handling. On any LLM step failure, write `.work/last-error.md` with step name + cause + suggested recovery action ("rerun with `--force-redo`", "manually delete `.work/scene-plan.md`"). Atomic writes (Finding-2 already covers) prevent half-writes; this covers post-write logical inconsistency.

---

## Verified Decisions Touched (Do NOT auto-reverse)

Per the user's explicit confirmations, these red-team findings do NOT recommend reversing:
- Hybrid 200-300 word sectioned image format (Finding-1 + 3 affect implementation, not format)
- Google 5-part video formula (Finding-24 questions Veo3 syntax detail, not the formula choice)
- Verbatim Identity Anchor (Finding-6 + 11 ADD enforcement, do not weaken to paraphrase)
- Reference image pattern deferred to v2 (no finding touches this)
- đam mỹ/ngôn tình BLOCKED (Finding-12 honest about limits, does not unblock)

---

## Top 5 Critical Findings (must-fix before phase-01 starts)

1. **Finding #1 — assemble_outputs.py rewrite needed, not copy** — schema mismatch is a 1-day surprise that breaks all of phase-2's reuse claim. Fix plan wording now; defer file rewrite to phase-02 with clear new spec.

2. **Finding #2 — Resume cache invalidation missing** — silent wrong output on any input change. Add scene-plan hash to scene-NNN.md frontmatter; design now, costs 5 LOC vs hours of confused debugging later.

3. **Finding #3 — Image vs video scene file collision** — naming/numbering confusion in output `.txt` files will look like data loss to user. Decide separate vs combined files BEFORE writing assembler.

4. **Finding #4 — Wall-time budgets unrealistic** — 12-min medium and 25-min long are 2x optimistic. Either widen budgets honestly OR introduce batching design (5-scene-per-turn). User-facing promise that fails on first run damages trust.

5. **Finding #5 — Antigravity flag parsing is LLM-string-match, not argv** — every `--flag` is hope-based. Add explicit "Argument Parsing" block to .toml prompt (mirror proofreader pattern) and add negative-test in phase-05.

---

## Unresolved Questions

- Does Antigravity actually use `~/.gemini/` paths or its own dir? (Finding #21 — verify before phase-01)
- What is real Veo3 timestamp syntax? (Finding #24 — verify before phase-04)
- Should bible-augmenter use script-based append for byte-identity guarantee? (Finding #11 — user decision: trust LLM vs guarantee correctness with +30 LOC)
- Are test fixtures going to be synthetic or sourced? (Finding #15 — needs user direction before phase-05)
- Is multi-call latency batching (5-scene-per-turn) acceptable architectural change? (Finding #4 — user decision: keep current design with longer budget OR redesign for speed)
