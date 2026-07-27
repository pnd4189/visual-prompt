# Hướng Dẫn Sử Dụng — visual-prompt

> Skill tạo prompt ảnh grounded từ file truyện tiên hiệp / võ hiệp tiếng Việt
> (chọn được 1 trong 18 art style) trên Agy, Codex CLI, và Claude Code.

---

## 1. Skill này làm gì?

Bạn có 1 file truyện tiên hiệp / huyền huyễn / võ hiệp tiếng Việt (2k–18k từ,
phù hợp video 1–2 giờ audio). Không cần proofread trước — skill tự hiệu đính.
Bạn muốn làm video YouTube với khoảng 120-150 ảnh cho 1 giờ audio; video clip và
nhạc nền là các phần bật thêm khi cần.

`/visual-prompt <file.txt>` đọc truyện → mặc định tạo 2 file:
- `<file>_qa.txt` — bản truyện đã hiệu đính, đưa THẲNG vào TTS_Local đọc giọng
- `<file>_image_prompts.txt` — paste vào công cụ tạo ảnh để gen ảnh

Thêm `--video`/`--videos N` hoặc mô tả “tạo video prompt” để có video; thêm
`--music`/`--music N` hoặc “tạo music prompt” để có music.

Toàn bộ workflow do active Antigravity/Agy model điều khiển. Python chỉ làm I/O file.

---

## 2. Yêu cầu

- **Antigravity/Agy CLI** — đã cài và chạy được
- **Python 3.10+** (`python3 --version`)
- Active Agy model đủ mạnh (skill này dùng LLM nặng để plan + expand scenes)
- (Optional) `python-docx` nếu input là `.docx`: `pip install python-docx`

---

## 3. Cài đặt

### Linux / macOS

```bash
cd /path/to/visual-prompt
bash setup.sh
```

Script tạo symlink cho Agy (`~/.gemini`), Codex (`~/.agents/skills` và
`~/.codex/prompts`), và Claude Code (`~/.claude/skills`). Mở CLI tương ứng rồi
gọi lệnh như mục dưới.

### Windows (Admin / Developer Mode)

```cmd
cd C:\path\to\visual-prompt
setup.bat
```

Yêu cầu chạy với quyền Admin HOẶC bật Developer Mode (Settings → For Developers).

### Windows (Non-Admin)

`setup.bat` tự fallback sang `xcopy` nếu symlink fail. Mỗi lần update repo
phải chạy lại `setup.bat` để re-sync (xem [antigravity/INSTALL.md](antigravity/INSTALL.md)).

---

### Gọi trên từng CLI

- Agy: `/visual-prompt truyen.txt`
- Codex native skill: `$visual-prompt truyen.txt`
- Codex slash shim: `/prompts:visual-prompt truyen.txt`
- Claude Code: `/visual-prompt truyen.txt`

Codex dùng skill native để giữ context tốt nhất; slash shim chỉ chuyển nguyên
`$ARGUMENTS` vào skill. Claude dùng `disable-model-invocation: true`, nên skill
chỉ chạy khi người dùng gọi slash command rõ ràng. Các adapter đều trỏ về cùng
`commands/`, `prompts/`, `references/`, `scripts/`; không có ba workflow khác nhau.

---

## 4. Sử dụng cơ bản

```
/visual-prompt /path/to/truyen.txt
```

Skill chạy pipeline grounding (mặc định image-only):
1. Load chapters
2. **QA hiệu đính** (luôn chạy) — sửa chữ Trung/Anh sót, chính tả, câu dịch máy
   lủng củng, tách câu dài → `chapters_qa.json` + `<file>_qa.txt`
3. Trích xuất character bible (lưu cạnh file truyện); field ngoại hình thiếu
   bằng chứng được ghi `not stated`, không tự ước lượng tuổi/tóc/mặt/đạo cụ
4. Detect thể loại
5. **Chọn style** — gợi ý style theo thể loại + HỎI bạn chọn (Enter = #1, hoặc gõ
   id khác). Có `--style <id>` → bỏ qua hỏi. Xem mục §5 "Chọn style".
6. Tính số scene (mặc định: 120-150 ảnh; video chỉ khi có opt-in)
7. Plan + expand scenes (theo style đã chọn)
8. Video/music (chỉ khi đã bật bằng flag hoặc mô tả rõ)
9. Assemble các file output đã bật

**Kết quả** nằm cạnh file input:
- `truyen_qa.txt` (đưa vào TTS_Local — xem §6)
- `truyen_image_prompts.txt`
- `truyen_video_prompts.txt` (chỉ khi bật video)
- `truyen_music_prompts.txt` (chỉ khi bật music)
- `character-bible.md` (giữ lại cho lần sau)
- `.work/` (cache resume — không xoá nếu muốn re-run nhanh)

---

## 5. Sử dụng nâng cao

### Chọn style — 18 art style

Sau khi detect thể loại, skill gợi ý 1 style mặc định (#1) + vài lựa chọn khác,
rồi **HỎI bạn chọn**: nhấn Enter để dùng #1, hoặc gõ một id khác. Style đã chọn
áp dụng nhất quán cho TOÀN BỘ ảnh + video của run đó.

**Bỏ qua bước hỏi** bằng flag `--style <id>`:

```
/visual-prompt truyen.txt --style donghua-xianxia
```

Sai id → skill báo lỗi và liệt kê id hợp lệ. Chạy headless / không trả lời câu
hỏi → tự fallback về #1 (in cách override bằng `--style`). Đổi `--style` rồi chạy
lại → scene tự regenerate (cache bust theo style).

**Genre và style tách rời:** mọi style đều dùng được cho mọi thể loại; bảng dưới
chỉ là gợi ý mềm.

| Thể loại | Style #1 (mặc định) | Lựa chọn khác |
|---|---|---|
| tiên hiệp | `donghua-xianxia` | `painterly-realism-cinematic`, `game-cg-25d`, `ink-wash-stylized` |
| huyền huyễn | `dark-fantasy-modao` | `game-cg-25d`, `concept-art-cityscape`, `donghua-xianxia` |
| đô thị | `semi-realistic-digital-painting` | `manhua`, `scifi-donghua-kehuan` |
| cổ điển | `painterly-realism-cinematic` | `watercolor-gouache`, `ink-wash-stylized` |
| võ hiệp | `painterly-realism-cinematic` | `ink-wash-stylized`, `manhua` |

**18 style theo nhóm** (chi tiết: [references/style-catalog.md](references/style-catalog.md)):

- **narrative-safe (10)** — giữ nhất quán nhân vật tốt, dùng cho mọi scene:
  `donghua-xianxia`, `painterly-realism-cinematic`, `semi-realistic-digital-painting`,
  `light-novel-moe`, `concept-art-cityscape`, `dark-fantasy-modao`, `game-cg-25d`,
  `dark-zhiguai-folk-horror`, `scifi-donghua-kehuan`, `manhua`.
- **accent-title-card (7)** — look đẹp nhưng giữ mặt/dáng nhân vật KÉM qua nhiều
  scene; hợp title card / montage hơn: `ink-wash-stylized`, `flat-poster-silhouette`,
  `traditional-pattern-minimal`, `watercolor-gouache`, `minimalist-calligraphy-symbolic`,
  `folk-nianhua`, `photobash-epic-poster`.
- **video-oriented (1)** — thiết kế cho chuyển động, ảnh tĩnh trông dở:
  `ink-wash-animation`.

⚠ Chọn style nhóm accent/video cho cả run → nhân vật dễ "đổi mặt" giữa các cảnh.
Skill sẽ cảnh báo lúc gợi ý. Muốn an toàn → chọn nhóm narrative-safe.

### `--series <name>` — Bộ truyện nhiều file

Khi làm 1 bộ nhiều file (mỗi file = 1 tập / 1 giờ audio), dùng cùng `--series`
để bible persist giữa các file → nhân vật consistent.

```
/visual-prompt truyen-tap-1.txt --series dai-dao-trieu-thien
/visual-prompt truyen-tap-2.txt --series dai-dao-trieu-thien
```

Bible lưu ở `~/.gemini/bibles/dai-dao-trieu-thien.md`. File tập 2 sẽ append
nhân vật mới, KHÔNG sửa nhân vật cũ.

### `--genre <name>` — Override thể loại

Nếu auto-detect sai (vd: chương đầu là flashback hiện đại của truyện tiên hiệp):

```
/visual-prompt truyen.txt --genre tien-hiep
```

Giá trị hỗ trợ: `tien-hiep`, `huyen-huyen`, `do-thi`, `co-dien`, `vo-hiep`.

### `--images N --video/--videos M` — Override số lượng

Mặc định chỉ có image: `N = clamp(round(wc/120), 120, 150)`, `M = 0`.
Muốn bật video tự động hoặc ép số khác:

```
/visual-prompt truyen.txt --images 30 --video
/visual-prompt truyen.txt --images 30 --videos 4
```

`--videos M` tự bật video và tôn trọng đúng M. Không truyền flag video thì video
không được tạo.

### `--music [N]` — Bật số loop nhạc nền

Music không chạy mặc định. Dùng `--music` để skill tự chia 3–5 vùng; dùng
`--music N` để ép số loop cụ thể:

```
/visual-prompt truyen.txt --music 6
```

`--music N` được tôn trọng ĐÚNG N, KHÔNG bị clamp (`--music 8` → 8 loop,
`--music 1` → 1 loop). Chỉ path tự động (không có flag) mới clamp về [3,5].

### `--force-redo` — Chạy lại từ đầu

Resume cache bỏ qua bước đã có file. Muốn re-gen toàn bộ:

```
/visual-prompt truyen.txt --force-redo
```

Xoá `.work/qa-chapter-*.md`, `.work/scene-*.md`, `.work/music-*.md` trước khi
vào các loop. Bible không bị xoá.

### Grounded mặc định + `--epic` / `--faithful`

> **Mặc định = grounded.** Mỗi row có `source_anchor` nguyên văn 6–24 từ từ đúng
> chapter. Active parent model được sáng tạo góc quay, bố cục, ánh sáng, bảng màu,
> texture và atmosphere riêng từng scene, nhưng không được thêm nhân vật, combat,
> địa điểm, đạo cụ, thời tiết hay kết quả không có trong nguồn.

```
/visual-prompt truyen.txt            # grounded + image-only
/visual-prompt truyen.txt --epic     # chỉ tăng treatment của chi tiết đã có
/visual-prompt truyen.txt --faithful # alias tương thích, vẫn grounded
```

- `--epic`: tăng chất lượng framing/lighting/scale cho chi tiết source-supported;
  không tạo quân đội/đám đông mới.
- `--faithful`: giữ tương thích với lệnh cũ; từ v0.11 mọi mode đều grounded.

> Plan/depth/similarity gates fail-closed: sau tối đa hai lượt sửa vẫn còn lỗi thì
> dừng và nêu scene ID, không “warn-and-ship”.

---

## 6. Cách dùng output

### TTS — đọc giọng từ `_qa.txt` (TTS_Local)

File `<truyen>_qa.txt` đã được hiệu đính sạch và CHÍNH LÀ input cho TTS_Local —
không cần file riêng. Tiêu đề chương (`Chương N: ...`) được giữ lại và sẽ được
đọc lên (có dấu chấm cuối để TTS ngắt nghỉ đúng).

```bash
cd /path/to/TTS_Local

# VieNeu (mặc định)
python tts_cli.py /path/to/truyen_qa.txt \
    --engine vieneu --voice "Xuân Vĩnh (Nam - Miền Nam)" --mp3

# VietVoice
python tts_cli.py /path/to/truyen_qa.txt \
    --engine vietvoice --mp3
```

`--mp3` xuất thêm file MP3 sẵn sàng cho YouTube. Bỏ `--voice` để dùng giọng mặc
định của engine; xem danh sách giọng trong TTS_Local.

### Công cụ tạo ảnh

1. Mở https://gemini.google.com → New chat → chọn model có image gen
2. Mở `truyen_image_prompts.txt`
3. Copy 1 block giữa 2 dòng `--- SCENE 001 ---` … `--- SCENE 002 ---`
4. Paste → đợi 4K render
5. Tải về, đặt tên `scene-001.png`

### Qwen-Image

Tương tự Gemini. Qwen chấp prompt CN/EN mixed, không cần dịch lại.

### ChatGPT (DALL-E)

1. Mở ChatGPT → Image tab (hoặc gõ "tạo ảnh:")
2. Paste block, **xoá dòng `Negative: ...`** (DALL-E không hỗ trợ negative)
3. Hoặc chuyển negatives thành "avoiding X, X" trong Style section

### Veo3 (video, trong Antigravity)

1. Mở Veo3 tab trong Antigravity
2. Mở `truyen_video_prompts.txt`
3. Copy 1 block `--- SCENE 007 ---`
4. Paste vào Veo3 prompt box → đợi 8s video
5. Note: ms-timestamps `[00:00-00:02.5]` được Veo3 honor; audio cue đã embed
   trong Style & Ambiance — KHÔNG cần paste audio riêng

### Seedance

Tương tự Veo3. Nếu prompt > 600 từ → trim phần Context.

### Lyria 3 — nhạc nền từ `_music_prompts.txt` (Lyria app)

File `<truyen>_music_prompts.txt` chứa N khối, mỗi khối là 1 prompt nhạc nền
instrumental cho 1 vùng cảm xúc của truyện.

1. Mở Lyria app → chọn Lyria 3 (music generation)
2. Mở `truyen_music_prompts.txt`
3. Copy lần lượt từng khối gồm một paragraph tiếng Anh và section `Tags:` ngay
   sau nó; các khối cách nhau bằng dòng trống.
4. Paste → Lyria tạo đoạn nhạc ~2-3 phút, loop được

**Bao nhiêu loop?** Music mặc định tắt. Khi đã bật bằng `--music` mà không ghi
số, skill dùng 4 loop (tự co giãn 3–5). Truyện dài / nhiều cao trào → dùng
`--music 5` hoặc hơn. Truyện ngắn / cảm xúc phẳng → `--music 3`.

**Đặt nhạc vào timeline:** thứ tự block khớp thứ tự region trong
`.work/music-plan.md`; dùng `chapter_start/chapter_end` ở đó để đặt nhạc.
**Sync thủ công** — skill không tự canh timeline.
Khi chạy batch bằng `run-folder.sh`, mapping và cache được giữ cạnh input trong
thư mục `<stem>_music-cache/music-plan.md` thay vì local `.work` đã dọn.
Batch chỉ skip khi `<stem>_visual-prompt-complete.json` còn khớp input, output,
cache, version, model, style và flags; bất kỳ thay đổi nào sẽ tự chạy lại file.

**Lưu ý giới hạn Lyria:** cuối prompt đã ép
`no vocals, no lyrics, instrumental only`, nhưng Lyria VẪN có thể tạo pad nghe
giống giọng người. Đây là giới hạn của model, không loại bỏ 100% được. Nếu đoạn
nào lẫn tiếng hát → re-generate hoặc chỉnh lại mood trong prompt.

**Resume nhạc:** vùng cảm xúc được lưu trong `.work/music-plan.md`. Chạy lại với
cùng input/genre/scene-plan/music count sẽ tái dùng đúng segmentation và chỉ
regen loop thiếu hoặc stale; `--force-redo` tạo lại cả music plan.

---

## 7. Workflow đề xuất

| Audio length | Wordcount | Images | Videos | Cadence |
|---|---|---|---|---|
| 1 giờ | ~9k từ | ~120 | ~20 | 1 prompt / ~30s audio slot |
| 2 giờ | ~18k từ | ~150 | ~25 | 1 prompt / ~45–50s audio slot |

**Lý do:** output nhiều hơn giúp tránh video audio quá tĩnh; editor vẫn có thể
chọn lọc hoặc dùng `--images` / `--videos` để chạy nhanh. Chi tiết:
[references/youtube-pacing-guide.md](references/youtube-pacing-guide.md).

---

## 8. Bộ truyện nhiều file (Series workflow)

Mục tiêu: nhân vật Tiểu Phàm trong file tập 1 phải nhìn GIỐNG nhân vật Tiểu
Phàm trong file tập 5 khi gen ảnh.

Cơ chế: **Identity Anchor verbatim** (xem
[references/identity-anchor-rules.md](references/identity-anchor-rules.md)).
Bible lưu đúng mô tả có trong nguồn, **paste nguyên văn** vào mỗi prompt Subject
section. Field chưa được truyện xác lập giữ `not stated`; skill không tự tạo nét
mặt, tuổi, trang phục hay signature prop để làm nhân vật “đẹp” hoặc “độc đáo”.

Với `--series`, pipeline còn duy trì
`~/.gemini/bibles/<series>-visual-history.md`. Similarity gate bắt copy-paste
giữa scene/loop trong run; history lưu camera, setting, action motif và music
intro/tag đã dùng để các file sau tránh lặp nguyên văn. Địa điểm vẫn được tái
xuất khi plot cần, nhưng phải mô tả bằng góc máy và chi tiết mới.

Quy trình:
```
# Lần đầu (tập 1) — tạo bible
/visual-prompt tap-1.txt --series ten-bo-truyen

# Các tập sau — append nhân vật mới, GIỮ NGUYÊN nhân vật cũ
/visual-prompt tap-2.txt --series ten-bo-truyen
/visual-prompt tap-3.txt --series ten-bo-truyen
```

Bible ở `~/.gemini/bibles/ten-bo-truyen.md`. Backup định kỳ:
```bash
cp -r ~/.gemini/bibles/ ~/backup-bibles/
```

---

## 9. Troubleshooting

### Lỗi: `Python not found`
Cài Python 3.10+: `apt install python3` (Linux), `brew install python3` (Mac),
https://python.org/downloads (Windows).

### Skill không autocomplete trong Antigravity
1. Check symlinks: `ls -la ~/.gemini/extensions/visual-prompt`
2. Re-run `bash setup.sh`
3. Restart Antigravity

### `.docx` input báo `python-docx not installed`
```bash
pip install python-docx
```

### Genre detect sai
Override: `--genre tien-hiep` (hoặc loại khác). Hoặc viết tay chương đầu rõ
keyword hơn (thêm "tu tiên", "luyện đan" vào mở đầu).

### Bible drift giữa các file series
Check `.work/bible-conflicts.md` — nếu có conflicts, skill đã giữ bible cũ
nhưng log lại để bạn review. Nếu muốn đổi mô tả nhân vật cho cả bộ → sửa tay
file `~/.gemini/bibles/<name>.md` rồi `--force-redo` toàn bộ files.

### LLM lặp scene gần nhau
Scene-planner có self-check uniqueness nhưng đôi khi miss. Sửa tay
`.work/scene-plan.md`, rồi chạy lại (không `--force-redo` để giữ scene khác).

---

## 10. FAQ

**Q: Skill này có hỗ trợ đam mỹ / ngôn tình không?**
A: KHÔNG. Skill refuse 2 thể loại này. Genre detector halt với VN message.
Lý do: ngoài scope, không nằm trong negative list / vocab tables.

**Q: Truyện fantasy phương Tây?**
A: KHÔNG. Visual vocab + negative lists được tune cho xianxia/wuxia. Nếu
dùng cho truyện Tây, ảnh ra sẽ kỳ lạ (anti-medieval armor sẽ block).

**Q: Tôi muốn thay đổi format prompt — sửa ở đâu?**
A: `references/visual-prompt-template.md` — đây là spec master. Mọi prompt
follow file này.

**Q: Làm sao backup bible?**
A: `cp -r ~/.gemini/bibles/ ~/backup-bibles/`. Bibles user-local, không sync
cloud (privacy).

**Q: Muốn add genre mới (vd: thanh xuyên — xuyên không thời gian)?**
A: Sửa `references/genre-keywords.md` thêm 1 section, sửa
`references/negative-lists.md` thêm 1 block genre-specific, sửa
`prompts/genre-detector.md` thêm vào allowlist.

**Q: Veo3 truncate video clip của tôi.**
A: Check prompt body ≤3800 ký tự + 2–3 beats + tổng ≤8.0s. Nếu tool cụ thể vẫn
truncate thì trim `Context` trước.

**Q: Có thiếu FAQ — báo ở đâu?**
A: Open issue tại GitHub repo (link trong README.md).
