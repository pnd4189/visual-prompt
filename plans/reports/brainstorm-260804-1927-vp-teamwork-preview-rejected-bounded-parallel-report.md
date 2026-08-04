# Brainstorm — /teamwork-preview auto-trigger cho /visual-prompt: REJECTED; chạy bounded-parallel coordinator thay thế

Date: 2026-08-04 19:27 · Mode: ultrathink · Status: APPROVED (vehicle A)
Related: audit-260804-1910 (gates/speed), plan 260729-1645 (bounded-parallel), researcher-260729 (agy subagent review)

## 1. Problem-first inversion

**Đề xuất mang vào (solution):** gói Gemini Ultra quota thoải mái → cho skill /visual-prompt chạy trên agy CLI auto-trigger /teamwork-preview để triệu hồi đội subagent worker tăng tốc.

**Vấn đề thật đứng sau:** Pass-2 (expand 120–150 scene) serial bởi 1 model chiếm ~80–90% wall-clock mỗi file; quota song song đang bỏ phí. Audit 260804-1910 đã xác nhận gates không phải nút thắt.

**Evidence:**
- /teamwork-preview có thật: 87 lần dùng trong `~/.gemini/antigravity-cli/history.jsonl`; binary agy (bản 8/3) chứa họ agent `teamwork_preview_explorer/reviewer/auditor/challenger/test_writer/spec_miner/victory_audit` + flag `enable_teamwork_subagent`. Cơ chế = prompt-driven in-skill orchestration (model cha gọi subagent built-in), KHÔNG có CLI API public (`agy --help`/`agy agents` không lộ spawn/worker).
- Researcher report 260729: agy không có subagent API public; contract cấm in-skill delegation.
- RULE 0 (TOML) cấm subagent/team/delegation — ra đời sau incident Agy tự chế workflow, vượt scene-planner, giấu generator trong scripts/. RULE 0 là anti-bypass, không phải anti-quota.
- Batch chạy `agy -p` one-shot; yield-turn = exit (incident trong memory). Không bằng chứng teamwork (đa turn) sống sót trong `-p` — suy luận, chưa verify.

**Assumption test (của đề xuất):**
- "Quota thoải mái → parallel thoải mái" → sai một phần: trần thực tế là rate-limit/phút, không phải quota tháng.
- "Teamwork = tăng tốc miễn phí" → sai: worker built-in mù contract visual-prompt; gate bắt rác → rewrite loop → HALT → retry cả file; net có thể âm.
- "Gate vẫn bảo vệ chất lượng" → đúng nhưng gate đo outcome, không đo provenance: subagent viết scene vẫn pass `check_run_legit` → bypass kiểu mới KHÔNG bị phát hiện.

## 2. Phương án đánh giá

| | Tốc độ | Chất lượng | Headless batch | Chi phí | Verdict |
|---|---|---|---|---|---|
| A. Bounded-parallel coordinator (plan 260729-1645) | ~×3 Pass-2, trần = rate-limit/phút | giữ nguyên: worker = phiên agy đầy đủ contract, gate ở coordinator | ✓ (`agy -p`) | ~8h theo plan | **CHỌN** |
| B. Auto-trigger /teamwork-preview trong run | unknown, rủi ro net âm | rủi ro cao: worker mù contract, không write fence, .work race | ✗ (khả năng cao chết ở yield-turn) | tưởng 0đ, thực tế phải vá contract+gate+fence+provenance | **BÁC** |
| C. Status quo + dedup gate (audit 260804-1910) | tiết kiệm phút, không phải giờ | giữ nguyên | ✓ | rất nhỏ | để dành, track riêng |

## 3. Lý do bác B (ghi lại — không lật lại nếu không có evidence mới)

1. Vi phạm RULE 0 đúng cơ chế đã từng hỏng (delegation bởi model đang chạy).
2. Worker teamwork không đọc strict-generation-contract/anchor/10-section/frontmatter/cache-key → rác → gate bắt → rewrite/HALT/retry → chậm hơn.
3. Không write fence/ownership manifest cho `.work/` (plan bounded-parallel phải thiết kế riêng phần này).
4. Headless `-p` (path batch, nơi cần tốc độ nhất) không được chứng minh; rủi ro yield-turn giết cả run.
5. Provenance gap: gate hiện tại không phân biệt parent-model vs subagent viết scene → bypass không bị phát hiện.

## 4. Design được duyệt (vehicle A)

Giữ nguyên kiến trúc plan 260729-1645, chốt thêm:

- Opt-in `VP_WORKERS=N` (run-folder.sh): **mặc định 3**, cap theo số scene còn lại; không set = serial byte-for-byte không đổi.
- Coordinator: freeze hash bundle (qa/bible/style/plan/visual-history) → chia dải scene-id rời → spawn N phiên `agy -p` worker submode → join (đủ coverage, không trùng, không file lạ) → chạy mọi gate hiện có không suy giảm → completion marker chỉ sau join + gates.
- Worker submode (mới trong TOML): nhận frozen manifest + dải id; CHỈ viết scene-NNN.md được giao; mismatch/stale/timeout/unexpected-write = fail-closed; không chạy music/assemble/history/marker.
- RULE 0 giữ nguyên cho model trong run; delegation chỉ ở runner level (bash spawn). Ghi rõ ngoại lệ này trong TOML + adapters.

**Bổ sung: Phase 0 — đóng plan v0.10** (prerequisite, plan 260729 đang `blockedBy`):
1. Commit WIP +636 dòng (targeted repair batches, `--report-json`, tests).
2. Phase-01 v0.10: dọn 18 dir rác root vào quarantine.
3. Phase-07 v0.10: sync version/status plan + memory; kỷ luật release.

**Acceptance:**
1. Serial path không đổi khi thiếu VP_WORKERS (khóa bằng test trước khi code).
2. Worker chỉ viết file trong dải; collision/stale/timeout/unexpected-write fail-closed, không leak state.
3. Marker chỉ sau join + gates; partial completion không che missing ID.
4. Benchmark file thật: Pass-2 ≥ ~1.8× với 3 worker; hụt do rate-limit → tune VP_WORKERS, không nới gate.
5. 40 test contract + test protocol worker mới pass.

**Risks:** rate-limit/phút (429 → bounded retry + serial fallback); overhead startup session agy với file nhỏ (cap worker theo scene count); worker submode = contract surface mới → sync TOML + 2 adapters + CANONICAL_SCRIPTS nếu thêm validator.

**Success metrics:** wall-clock Pass-2/file (serial vs 3w); first-pass gate pass rate không đổi; 0 provenance violation; similarity outcomes như nhau.

**Out of scope:** mọi tích hợp /teamwork-preview; parallel QA/bible/plan/music; khuyến nghị tốc độ audit 260804-1910 (track riêng).

## 5. Next steps

1. Report này + cập nhật plan 260729 (Phase 0 + decisions) — xong trong session.
2. `/ck:cook` plan 260729 (bắt đầu từ Phase 0).
3. Phase 4 benchmark quyết định giữ 3 worker hay tune.

## 6. Open questions

- Teamwork có sống sót trong `-p` multi-turn không? Không cần trả lời cho vehicle A; chỉ đáng spike thủ công nếu sau này muốn xét lại B (đã bị bác).
- Rate-limit/phút thực tế của Gemini 3.1 Pro (High) trên Ultra với 3 session song song — benchmark phase 4 trả lời.
