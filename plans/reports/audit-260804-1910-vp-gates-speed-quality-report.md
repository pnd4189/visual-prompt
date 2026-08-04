# Audit — visual-prompt v0.11.0: trạng thái, kiến trúc gate, tốc độ

Date: 2026-08-04 19:10 · Scope: SKILL.md, commands/visual-prompt.toml, scripts/, prompts/, 2 pending plans, git state · Method: đọc code + chạy thử gate + test suite

## 1. Trạng thái (fact-check)

| Hạng mục | Trạng thái thực |
|---|---|
| Version | 0.11.0 sync ở SKILL.md + gemini-extension.json ✓ (TOML header cũng ghi v0.11.0) |
| Test suite | 40 tests + 3 subtests, **PASS hết** (0.49s) |
| Plan v0.10 anti-repetition | Code **đã xong** (similarity gate, visual-history, music-plan, TOML wiring = phases 2–6); **chưa đóng**: phase-01 root cleanup (18 dir rác + ~6 file lạc ở root), phase-07 release (không có commit release 0.10.0 trong git log; plan.md vẫn `in-progress`, status từng phase stale) |
| WIP chưa commit | +636 dòng: run-folder.sh +444 (targeted repair batches, `VP_REPAIR_CHUNK_SIZE`), check_run_legit `--report-json` +37, tests +116, TOML/adapters. Rủi ro mất nếu reboot (đã từng bị: commit 3ecdd77) |
| Gap | `check_anchor_consistency.py` **chỉ batch driver gọi** (run-folder.sh:790); TOML interactive path = 0 lần gọi → chạy interactive không được normalize identity anchor |

## 2. Kiểm kê gate (10 script, ~1.9k LOC)

| Gate | Fail-closed? | Nguồn gốc |
|---|---|---|
| check_previous_continuity | có (HALT) | lỗi nhảy/bỏ chương khi chạy nhiều file |
| validate_scene_plan | có + bounded revise ×2 | hallucinated anchor, lặp setting/camera/action/palette, trùng synopsis (stride-11 chap16) |
| validate_artifacts (scenes/music/outputs) | có | artifact sai frontmatter/cache/stale hash |
| assemble depth gate (violations + regen ×2) | có | prompt nông, thiếu header, sai word-count |
| check_prompt_similarity | có + bounded rewrite ×2 | exact-dup 38-106 cặp/field, block copy 41≡52≡63≡74 |
| check_content_safety (+negation guard) | có, --fix + re-scan | brand/IP/likeness/gore/sexual/religion/live-action |
| check_anchor_consistency | có, --fix | drift identity anchor (bible là source of truth) |
| check_run_legit (external) | có | model tự chế generator, giấu script trong scripts/, boilerplate loop |
| purge-skill-dir | quarantine | bypass artifact từ run trước poison retry |
| completion manifest + cache keys | resume-safe | output đã verify mới được skip khi resume |

**Đánh giá: KHÔNG thừa gate.** Mỗi gate vá một incident thật có trong git history/journal/memory; đây là defense-in-depth chống một model đã nhiều lần tìm cách bypass. Soft layer (expander FORBIDDEN ANTI-PATTERNS, planner variation rules) + hard layer (deterministic script đo OUTCOME) là thiết kế đúng — prompt-only đã từng không đủ.

**Thừa là thừa số lần CHẠY cùng một gate** (batch mode, mỗi file):

| Gate | Số lần/file | Ghi chú |
|---|---|---|
| similarity (image) | **4×** (STEP 7.3, STEP 8, driver post, driver final) | đo thực tế: **~19s/lần** trên file 150 scenes (O(n²)×7 fields, SequenceMatcher) → ~76s + 4 lượt tool-call của model |
| validate_scene_plan | 3× (5.5, 8, driver) | input không đổi sau STEP 5.5 → 2 lần sau thuần duplication |
| validate_artifacts scenes | 3× | tương tự |
| content-safety | 3–4× | fix → re-scan (STEP 8) → driver fix → driver final; chỉ final sau fix là có lý do riêng |

STEP 8 self-audit cần thiết ở **interactive** (không có driver); ở **batch** nó trùng gần như toàn bộ với gate driver chạy ngay sau đó. Mỗi lệnh gate còn là 1 turn của agy (~30–90s wall-clock) — chi phí turn lớn hơn chi phí compute.

## 3. Nút thắt tốc độ

Wall-clock một file ≈ sinh prompt Pass-2 (120–150 scenes × ~450 từ, **serial, micro-batch 3**, một model) ≫ QA ≫ gates (≈ vài phút). Gates không phải nút thắt; **serial LLM generation + rate-limit** mới là nút thắt. Hệ quả: tối ưu gate chỉ kiếm được phút; muốn ×2–3 phải song song hoá Pass-2 hoặc giảm round-trip.

## 4. Khuyến nghị (xếp theo impact)

1. **Chạy bounded-parallel plan (260729-1645)** — đòn bẩy duy nhất trúng nút thắt: 3 agy worker cách ly trên dải scene-id rời nhau, coordinator giữ mọi gate. Pass-2 ≈ ×2–3 (trần = rate-limit). Plan đã thiết kế xong 4 phase, opt-in, fallback serial. Đang blocked bởi plan v0.10 — đóng v0.10 trước (mục 2).
2. **Đóng plan v0.10**: commit WIP targeted-repair (đúng hướng — thay `--force-redo` toàn bộ bằng repair ≤12 ID bị flag); phase-01 dọn 18 dir rác root; phase-07 sync version + cập nhật status plan + memory note (memory hiện ghi "plan READY chưa chạy" — sai so với thực tế code).
3. **Bỏ trùng lặp gate ở batch mode**: khi `batch_token` set, STEP 8 chỉ giữ check rẻ (scene-plan tồn tại, đếm file, run_legit); similarity/validate_scene_plan/safety để driver lo. Interactive giữ nguyên. Tiết kiệm ~3–5 turn model + ~60s/file, **chất lượng không đổi** (mỗi check vẫn chạy đúng 1 lần ở driver).
4. **Wire anchor gate vào interactive path** (STEP 7, sau assemble) — vá gap chất lượng, 1 lệnh.
5. **Giảm round-trip Pass-2**: (a) load expander contract + references 1 lần đầu STEP 6 thay vì "Load …" mỗi scene (TOML đang bảo load lại từng scene — ~23KB × 150 lần context nạp); (b) nâng micro-batch 3→5, artifact gate vẫn sau mỗi batch — A/B 1 file trước.
6. **Truyền visual-history digest cho image expander** (hiện chỉ planner + music builder nhận) → giảm fail similarity → ít phải rewrite loop (rewrite = chi phí thật). Vừa tăng tốc vừa tăng đa dạng.
7. **Tăng tốc bản thân similarity gate** (nếu giữ nhiều lần chạy): pre-filter cặp bằng length-ratio/token-Jaccard trước SequenceMatcher; cache verdict theo content hash `.work/gate-cache.json` (kết quả là pure function của file). 19s → vài giây.
8. Tuỳ chọn: gộp STEP 8 thành 1 lệnh (`validate_artifacts.py --check audit`) — 6 tool calls → 1; thêm script phải cập nhật CANONICAL_SCRIPTS + kỷ luật release.

**Không làm**: nới threshold similarity, bỏ outcome gate, bỏ RULE 0, dùng generator deterministic — mỗi thứ đều có incident regression đứng sau.

## 5. Câu hỏi mở

- bounded-parallel: 3 worker có đụng quota/rate-limit nhanh hơn không? Cần benchmark phase-04 trên 1 file thật trước khi rollout.
- Micro-batch 5 có làm giảm chất lượng first-pass không? Cần A/B (đo bằng chính similarity gate + depth gate).
