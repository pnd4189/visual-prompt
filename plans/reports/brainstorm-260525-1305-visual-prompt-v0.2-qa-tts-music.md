# Brainstorm — visual-prompt v0.2 (QA gate + TTS file + Lyria music prompts)

Date: 2026-05-25 · Status: APPROVED · Next: /ck:plan

## Problem statement

visual-prompt v0.1 giả định input đã proofread, chỉ xuất image + video prompts.
User cần 3 bổ sung để pipeline tự đủ end-to-end cho video audio truyện YouTube:

1. **QA gate đầu pipeline** — tự quét file, dịch nốt ký tự Trung/Anh sót, sửa
   chính tả/ngữ pháp, mượt câu dịch máy; mọi bước sau lấy bản đã QA làm căn cứ.
2. **File TTS** — bản truyện sạch nạp vào TTS_Local (VieNeu + VietVoice) tạo audio.
3. **Prompt nhạc nền Lyria** — instrumental không lời, match cảm xúc truyện, dán
   vào Lyria 3 (Gemini app).

Ràng buộc user: KHÔNG copy codebase/workflow của Grammar_check & TTS_Local.

## Verified facts (scout + research)

- **Kiến trúc v0.1:** LLM-driven (Gemini Ultra/Antigravity loop driver), Python chỉ I/O.
  Pipeline 7 bước trong `commands/visual-prompt.toml`. Cache resume-safe SHA1.
- **TTS ngắt nghỉ:** VieNeu & VietVoice dùng chung `text_processor.split_text()` —
  ngắt câu CHỈ theo dấu câu `.!?…`, identical. `clean_text()` gộp hết newline → 1 space
  (mọi format trong file bị xoá). Khác duy nhất: max_chars VieNeu 200 / VietVoice 500.
  → 1 file TTS chung dùng được cho cả 2. Verified `app/utils/text_processor.py:21-77`.
  Lưu ý: câu >200 ký tự → VieNeu cắt giữa câu; tiêu đề chương cần dấu chấm cuối để ngắt.
- **Lyria prompt (DeepMind/Google Cloud):** template
  `[Genre&style]+[Mood]+[Instrumentation]+[Tempo/rhythm]+"Instrumental."` ;
  khoá giọng = chữ `Instrumental.` + negative `no vocals/lyrics/singing`;
  Lyria 3 Pro ~3 phút, timestamp prompting `[00:00]...`; English cho kết quả tốt nhất.

## Decisions (locked)

| # | Quyết định | Chốt |
|---|-----------|------|
| 1 | File TTS | 1 file chung `_qa.txt` (ngắt nghỉ 2 engine identical) |
| 2 | Mức QA | Vừa phải — sửa lỗi + câu lủng củng, KHÔNG đổi cốt truyện |
| 3 | QA chạy | Luôn chạy, resume-safe per chapter, ghi `_qa.txt` |
| 4 | Tiêu đề chương | Giữ + thêm dấu chấm cuối (TTS ngắt nghỉ) |
| 5 | _qa vs _tts | Gộp — `_qa.txt` vừa là source vừa là file TTS |
| 6 | Chuẩn hóa số | Không — giữ nguyên số |
| 7 | Bản Lyria | Lyria 3 trong Gemini app (dán text, prose English) |
| 8 | Số loop nhạc | Thích ứng 3-5 theo cảm xúc, mặc định 4, `--music N` override |
| 9 | Độ dài clip | ~2-3 phút, "seamless loop, no fade out" |

## Final design — visual-prompt v0.2

### Pipeline (chèn 2 step)
```
STEP 0   Flag parse (+ --music N)
STEP 1   Load → chapters.json
STEP 1.5 ★ QA PROOFREAD → chapters_qa.json + <stem>_qa.txt
STEP 2-5 Bible / Genre / Scene count / Scene plan  (đọc chapters_qa.json)
STEP 6   Expand scenes
STEP 6.5 ★ MUSIC PROMPTS (tái dùng genre + scene-plan) → 3-5 mood region
STEP 7   Assemble → image + video + music .txt
```

### Output — 4 file cạnh input
- `<stem>_qa.txt` ★ — truyện QA sạch, source + file TTS (giữ tiêu đề chương + dấu chấm)
- `<stem>_image_prompts.txt` (giữ)
- `<stem>_video_prompts.txt` (giữ)
- `<stem>_music_prompts.txt` ★ — 3-5 block: nhãn VN + prompt Lyria English instrumental + BPM/key

### Cơ chế nhạc match cảm xúc
Tái dùng `genre-detector` (palette nhạc cụ theo thể loại) + `scene-plan.md` (beat cảm xúc)
→ LLM gom scene/chapter thành 3-5 vùng mood liền kề (clamp, default 4, --music override)
→ mỗi vùng 1 prompt Lyria English instrumental + negative prompt khoá giọng hát.

### File tạo / sửa
Tạo (4): `prompts/qa-proofread.md`, `scripts/assemble_qa.py`,
`prompts/music-prompt-builder.md`, `references/music-mood-mapping.md`.
Sửa (4-5): `commands/visual-prompt.toml` (flag + STEP 1.5/6.5 + qa_hash + summary),
`scripts/assemble_outputs.py` (+ music-*.md → _music_prompts.txt),
`SKILL.md`, `HUONG-DAN-SU-DUNG.md`, (tùy) `scripts/calc_scene_count.py` (wc từ QA).

### Cache & resume
- QA: `.work/qa-chapter-NNN.md`, key `sha1(input_hash + chapter_text)`;
  `qa_hash = sha1(chapters_qa.json)` thay `input_hash` ở cache downstream.
- Music: `.work/music-NNN.md`, key `sha1(qa_hash + genre + plan_hash + region_spec)`.
- `--force-redo` xoá `qa-chapter-*` + `music-*`.

## Risks / limitations

1. Lyria KHÔNG 100% chắc instrumental — prompt + negative chỉ giảm thiểu, không khoá
   tuyệt đối output model. (User yêu cầu "tuyệt đối không lời" — kiểm soát ở mức prompt.)
2. Lyria 3 Gemini app clip có thể < 3 phút → có thể phải regenerate/ghép.
3. Đồng bộ nhạc với timeline audio là thủ công (chỉ ghi "dùng cho Chương X-Y").
4. QA "vừa phải" ranh giới mượt-câu vs đổi-nghĩa → prompt QA cần ví dụ + cấm rõ
   (không thêm/bớt tình tiết, đổi tên riêng, đổi số liệu).
5. QA luôn chạy kể cả input sạch → tốn 1 lượt LLM (user chấp nhận).

## Success criteria

- Chạy `/visual-prompt input.txt` → 4 file output, không lỗi.
- `_qa.txt`: không còn ký tự Trung/pinyin/English sót; câu mượt; tiêu đề chương có dấu chấm;
  số giữ nguyên; nạp `tts_cli.py --engine vieneu/vietvoice` ra audio sạch.
- `_music_prompts.txt`: 3-5 block, mỗi block English instrumental + negative prompt khoá giọng,
  mood khớp diễn biến truyện, dán Lyria 3 chạy được.
- Image/video prompts vẫn đúng như v0.1, nay lấy từ text đã QA.
- Cache: chạy lại không regenerate khi input/bible/plan không đổi; đổi input → QA + downstream regenerate.

## Constraints giữ vững
LLM-driven, Python chỉ I/O · không copy Grammar_check & TTS_Local · không dep nặng · không file `_v2`.

## Open questions
Không — 9 quyết định đã chốt. Cân nhắc tương lai (ngoài v0.2): `--skip-qa`, chuẩn hóa số cho TTS.
