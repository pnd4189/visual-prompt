# Brainstorm Report — visual-prompt 0.10.0: anti-repetition + reliability upgrade (agy CLI)

Date: 2026-07-14 | Mode: HITL (user-selected) | Scope: P0 + P1 + cleanup (user-approved)
Prior context: /fix diagnosis 2026-07-13, ultrathink review 2026-07-14, 0.9.2 allowlist gate (commit 435840a).

## 1. Problem statement

Skill /visual-prompt (agy CLI, symlink-installed, batch qua run-folder.sh) sinh image/music
prompt **lặp, dập khuôn, copy-paste** khi xử lý file dài (120-150 scene). Đồng thời còn
2 điểm tin cậy: music resume không deterministic, retry batch đốt 4h vì force-redo toàn phần.
Mục tiêu: nâng cấp kiến trúc để output sáng tạo/đa dạng ở mức tối ưu, model không thể
"lười" qua mặt, chi phí retry thấp.

## 2. Evidence (đo được, không phỏng đoán)

- `full_report.md` (audit thủ công file chap16, 120 scenes, threshold 0.6, difflib+tfidf):
  - Camera: 38 cặp trùng 100%, 194 cặp ≥0.6 / 7140 cặp
  - Setting: 106 exact / 108 cặp ≥0.6; Atmosphere: 106 exact
  - Pattern trùng theo stride +11: scene 41≡52≡63≡74, 42≡53≡64... (copy nguyên block)
- `validate_scene_plan.py`: WINDOW=10 (stride 11 lọt), chỉ so tag+characters, KHÔNG so synopsis.
- Depth gate + check_run_legit: chỉ đo word-count/header/ngram-trong-block/video-identical —
  exact-dup Camera/Setting GIỮA các scene lọt qua mọi lớp hiện có.
- `prompt-expander-image.md:168-178`: chỉ có ràng buộc mềm (self-check #7/#9), model bỏ qua.
- Vá thủ công đang treo uncommitted (+210 dòng): hardcode avoid-list camera/setting/action/
  music-tag CỦA RIÊNG bộ truyện đang chạy vào prompt dùng chung → phình context (34KB TOML +
  10KB planner), sai cho series khác, chết cứng không tự cập nhật. Kiến trúc sai, phải thay.
- SKILL.md limitation chính thức: "Music resume is best-effort" — segmentation do LLM chia lại
  mỗi run, không persist.

## 3. Root causes

1. Plan gate mù dup không-liền-kề + không so nội dung synopsis (stride 11 evade window 10).
2. Không có gate similarity chéo-scene nào sau assemble (mọi gate hiện có đo thứ khác).
3. Expander constraint mềm — LLM "tiết kiệm token" khi context dài (context degradation).
4. Chống lặp cross-run làm bằng hardcode series-specific trong prompt chung (sai chỗ).
5. Music segmentation không persist → resume vô nghĩa.

## 4. Approaches evaluated

| Approach | Pros | Cons | Verdict |
|---|---|---|---|
| A. Chỉ siết prompt constraint | rẻ, nhanh | model lười vẫn lờ; đã chứng minh thất bại (self-check #7 có sẵn mà vẫn dup 100%) | ❌ |
| B. Gate deterministic đo OUTCOME + rewrite loop + history động | model không thương lượng được; gian lận không có lãi; đúng trajectory 0.9.x | tốn ~1 script + wiring | ✅ chọn |
| C. Refactor lớn TOML 34KB | giảm degradation | rủi ro regression cao, lợi mơ hồ, YAGNI | ❌ hoãn; kỷ luật "enforcement mới = gate, không phình TOML" |

## 5. Final solution (đã qua ultrathink review, 6 refinement)

### 5.1 Script mới `scripts/check_prompt_similarity.py` (hấp thụ check_similarity.py đã proven)
- So 7 field/scene-pair (Camera, Story DNA, Setting, Composition, Action/Energy,
  Lighting/Color, Atmosphere); loại trừ Subject/Style/Negative (verbatim by-design).
- Sim = max(difflib.ratio, tfidf cosine); prefilter `quick_ratio()` (O(n²) 150 scene ~78k cặp).
- Parser fix 2 bug bản gốc: chỉ nhận 10 header đã biết (plain + `**bold**`) làm field,
  dòng `X:` lạ = continuation (Foreground:/Midground: không bị tách nhầm field).
- **Policy (user-approved + refinement chống evasion "đổi vài chữ")**:
  - VIOLATION (exit 2): `pair_copy` = 1 cặp scene có ≥2 field sim ≥0.95 (fingerprint copy
    nguyên scene), FAIL khi ≥2 cặp; HOẶC `field_dup_flood` = 1 field có ≥5 cặp exact (≥0.995).
  - WARNING (exit 0): cặp sim 0.60–0.95 — log/JSON only, không chặn batch.
  - Flags: `--soft 0.60 --near 0.95 --max-pair-copies 1 --max-exact-per-field 4`.
- `--music`: pairwise body ≥0.75 + trùng 8 từ mở đầu = violation; tag-overlap >70% = warning.
- `--video` (optional, rẻ): pairwise video body — vá lỗ gate legit chỉ FAIL >50% identical.
- `--extract-history`: chưng cất Camera line + Setting câu đầu + action motif + music intro/tags
  từ output cuối → append + dedupe + rolling cap ~150 dòng/section vào visual-history.
- JSON out {ok, violations[], warnings[], stats, rewrite_scene_ids[], banned_phrases[]}.

### 5.2 Vá gate hiện có
- `validate_scene_plan.py`: thêm `duplicate_synopsis` — pairwise synopsis TOÀN plan (mọi
  khoảng cách, difflib ≥0.8, quick_ratio prefilter). Bắt stride-N ngay Pass 1 (trước khi tốn
  quota expand). Wire loại violation mới vào revise contract STEP 5.5 (TOML).
- `check_run_legit.py`: thêm `check_prompt_similarity.py` vào CANONICAL_SCRIPTS (bắt buộc,
  nếu quên purge gate sẽ tự cách ly script mới — hai hệ thống đá nhau).

### 5.3 Visual-history động theo series (thay hardcode)
- File `~/.gemini/bibles/<series>-visual-history.md` (trong --add-dir sẵn của driver);
  sections: camera framings / settings / action motifs / music intros / music tags.
- STEP 7.8 (TOML, sau content-safety, chỉ khi --series): gọi `--extract-history` (I/O thuần,
  hợp lệ RULE 0). Không có --series → skip.
- `scene-planner.md` + `music-prompt-builder.md`: XÓA hardcode Mã-Lực-Thuật lists; GIỮ rule
  generic session trước (HARD DIVERSITY RULE, template-là-sườn-nội-dung, General Instructions);
  thêm "đọc visual-history nếu tồn tại". **Semantics quan trọng**: cấm dùng lại NGUYÊN VĂN
  mô tả/motif cũ — địa điểm tái xuất hợp lệ phải tả lại bằng góc máy + chi tiết MỚI
  (không cấm địa điểm).

### 5.4 Expander hardening (`prompt-expander-image.md`)
- Ràng buộc cứng: cấm reuse nguyên câu/cụm >8 từ từ scene khác (mọi section trừ Subject
  anchor/Style/Negative); Camera chọn theo beat, cấm xoay vòng 1 câu; Story DNA/Atmosphere =
  nhịp động khoảnh khắc, cấm summary tĩnh chương. Self-check #10: trùng nguyên câu với scene
  đã viết trong batch → REWRITE. (Cross-batch dup: subagent không thấy nhau → STEP 7.3 bắt.)

### 5.5 Pipeline wiring (TOML)
- STEP 7.3 SIMILARITY GATE: sau depth gate, TRƯỚC content-safety --fix (rewrite rồi mới safety,
  không mất safety edits). Loop bounded ≤2: violations → rm scene bị flag (giữ scene id nhỏ
  nhất mỗi cụm, rewrite các bản sau) → re-expand KÈM banned_phrases (bắt buộc, ép phân kỳ —
  chống loop không hội tụ khi input giống nhau) → re-assemble → re-check. Sau 2 lượt → WARN
  + ship (nhất quán depth gate). Music check tương tự sau STEP 6.5.
- STEP 8 self-audit: thêm lệnh chạy similarity check (model-side; driver vẫn là source of truth).

### 5.6 Music-plan persistence (P1 #5 — đóng limitation chính thức)
- STEP 6.5 đổi: LLM chia vùng 1 lần → ghi `.work/music-plan.md` (frontmatter cache_key =
  sha1(qa_hash+genre+plan_hash+music_n); body = bảng region {loop_index, chapter_start,
  chapter_end, mood}). Run sau: cache match → tái dùng segmentation, chỉ regenerate loop
  thiếu/stale. `--force-redo` xóa cả music-plan.md. Xóa dòng limitation trong SKILL.md.
- `validate_artifacts.py --check music` đọc expected từ music-plan nếu có.

### 5.7 Driver `run-folder.sh` (P1 #6)
- Sau legit gate: chạy similarity gate (image + music [+video nếu có]).
- Phân loại retry: legit-gate FAIL / thiếu output → `--force-redo` (như cũ); CHỈ similarity
  FAIL → re-run KHÔNG force (resume cache, STEP 7.3 rewrite đúng scene bị flag — rẻ ~95%).
  Chung cap 3 attempts → die (reject, không ship rác).

### 5.8 Version + cleanup
- Bump 0.10.0: SKILL.md + gemini-extension.json + TOML header; SKILL.md ghi gate mới +
  visual-history + bỏ music-resume limitation.
- Quarantine `.quarantine-260713/`: toàn bộ untracked rác root (55 mục, trừ plans/) — gồm
  cả generator.py/generate_prompts.py (nghi bypass artifact session thủ công).
- 2 commit: (1) dọn rác + absorb check_similarity, (2) feature 0.10.0.

## 6. Compliance matrix (agy non-compliance vectors)

| Vector | Sau 0.10.0 |
|---|---|
| Skip planner / tự chế orchestration | ✅ chặn (0.9.2) |
| Generator giấu trong scripts//root/.work | ✅ chặn (0.9.2 allowlist + purge) |
| Copy-paste template giữa scene (plan/image/music) | ✅ outcome-gate 3 tầng: plan → STEP 7.3 → driver |
| Đổi vài chữ lách gate | ✅ near-exact 0.95 + pair_copy fingerprint |
| Lặp motif giữa video trong series | ✅ visual-history động |
| Sim mềm 0.6–0.95 | ⚠️ WARN-only (user decision; siết sau khi có data) |
| Synonym-swap script tinh vi kéo sim <0.6 | ⚠️ residual — không gate nào chặn 100%; contract + audit + WARN log làm khó |
| Yield-turn giữa STEP 7.3/7.8 | ✅ driver bắt (thiếu output/gate fail → re-run resume) |

## 7. Risks

- False-positive FAIL trên run sạch: Camera line ngắn/formulaic có thể vô tình ≥0.95 →
  đã mitigate bằng pair_copy (cần ≥2 field cùng cặp) + count threshold. Theo dõi 2-3 run đầu.
- Rewrite loop không hội tụ khi plan rows giống nhau → plan gate mới chặn từ Pass 1 +
  banned_phrases ép phân kỳ; residual sau 2 lượt = WARN ship (bounded).
- Similarity gate chạy 2-3 lần/run — O(n²) có quick_ratio prefilter, ước <30s/lần, chấp nhận.
- STEP 7.3 thêm việc LLM cuối run → tăng nhẹ rủi ro yield-turn; driver re-run resume xử được.

## 8. Success metrics

1. Chạy script mới trên chính output chap16: FAIL với ~38 Camera exact-dup khớp full_report.md.
2. Fixture plan stride-11 → validate_scene_plan bắt duplicate_synopsis.
3. Run thật 1 file: exact-dup pairs = 0, pair_copy = 0; warnings 0.6-0.95 giảm rõ so baseline.
4. Visual-history được tạo/append sau run --series; run kế tiếp planner tránh motif cũ.
5. Re-run file đã xong: music không regenerate (cache music-plan hit).
6. py_compile/tomllib/bash -n sạch; batch 1 file end-to-end pass 4 gate.

## 9. Unresolved questions

- Ngưỡng near-exact 0.95 + max-pair-copies=1: cần tune sau 2-3 run thật (có flag override).
- Có nên FAIL band 0.6-0.95 sau khi đủ data? (để sau, user quyết).
- Windows copy-install: cần re-run setup.bat sau 0.10.0 (chỉ ảnh hưởng máy Windows nếu có).
