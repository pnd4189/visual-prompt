# Hướng Dẫn Sử Dụng — visual-prompt

> Skill Antigravity tạo prompt ảnh + video từ file truyện tiên hiệp / võ hiệp
> tiếng Việt (chọn được 1 trong 18 art style), dùng cho video audio YouTube.

---

## 1. Skill này làm gì?

Bạn có 1 file truyện tiên hiệp / huyền huyễn / võ hiệp tiếng Việt (2k–18k từ,
phù hợp video 1–2 giờ audio). Không cần proofread trước — skill tự hiệu đính.
Bạn muốn làm video YouTube với khoảng 120-150 ảnh + tối thiểu 20 video clip +
nhạc nền cho 1 giờ audio.

`/visual-prompt <file.txt>` đọc truyện → tạo 4 file:
- `<file>_qa.txt` — bản truyện đã hiệu đính, đưa THẲNG vào TTS_Local đọc giọng
- `<file>_image_prompts.txt` — paste vào công cụ tạo ảnh để gen ảnh
- `<file>_video_prompts.txt` — paste vào Veo3 / Seedance để gen video clip
- `<file>_music_prompts.txt` — paste vào Lyria 3 (Lyria app) để gen nhạc nền

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

Script tạo 3 symlink vào `~/.gemini/`. Mở Antigravity → gõ `/` → thấy
`visual-prompt` autocomplete.

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

## 4. Sử dụng cơ bản

```
/visual-prompt /path/to/truyen.txt
```

Skill chạy 9 bước (mất lâu hơn bản cũ vì mặc định tạo 120-150 ảnh và 20+ video):
1. Load chapters
2. **QA hiệu đính** (luôn chạy) — sửa chữ Trung/Anh sót, chính tả, câu dịch máy
   lủng củng, tách câu dài → `chapters_qa.json` + `<file>_qa.txt`
3. Trích xuất character bible (lưu cạnh file truyện)
4. Detect thể loại
5. **Chọn style** — gợi ý style theo thể loại + HỎI bạn chọn (Enter = #1, hoặc gõ
   id khác). Có `--style <id>` → bỏ qua hỏi. Xem mục §5 "Chọn style".
6. Tính số scene (mặc định: 120-150 ảnh, tối thiểu 20 video; override bằng flag)
7. Plan + expand scenes (theo style đã chọn)
8. **Music prompts** — chia arc cảm xúc thành N vùng (mặc định 4) → prompt Lyria
9. Assemble các file output

**Kết quả** nằm cạnh file input:
- `truyen_qa.txt` (đưa vào TTS_Local — xem §6)
- `truyen_image_prompts.txt`
- `truyen_video_prompts.txt`
- `truyen_music_prompts.txt`
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

### `--images N --videos M` — Override số lượng

Mặc định: `N = clamp(round(wc/120), 120, 150)`, `M = max(20, round(N/6))`.
Muốn ép số khác:

```
/visual-prompt truyen.txt --images 30 --videos 4
```

Có thể chỉ override 1 cái; cái còn lại vẫn dùng auto default từ wordcount/công thức
mặc định, không tự suy ra từ override kia.

### `--music N` — Số loop nhạc nền

Mặc định skill tự chia arc thành 4 vùng cảm xúc (tự co giãn trong khoảng 3–5).
Muốn ép số loop cụ thể:

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

### Spectacle mặc định + `--epic` / `--faithful`

> **Mặc định = spectacle (v0.6).** Đây là pipeline cho video YouTube giải trí, nên
> mặc định dựng cảnh giàu kịch tính: phong cảnh/map rộng, đông nhân vật trong
> khung, combat, đấu pháp, daoist magic — và ĐƯỢC PHÉP dramatize vượt nội dung
> chương để hình đẹp mắt, miễn giữ 3 rào: đúng thể loại (xianxia vẫn xianxia),
> đúng nhận diện nhân vật (anchor bible nguyên văn), không mâu thuẫn tình tiết đã
> nêu. Không còn xoay quanh mỗi nhân vật chính.

```
/visual-prompt truyen.txt            # spectacle (mặc định)
/visual-prompt truyen.txt --epic     # bơm scale mạnh hơn (map/đại quân/đám đông lớn)
/visual-prompt truyen.txt --faithful # trung thành text, KHÔNG bịa combat
```

- `--epic`: đẩy band spectacle lên một nấc — map cực rộng, quân đội/đám đông lớn,
  spectacle tối đa.
- `--faithful`: TẮT dramatize — đo mật độ hành động thật của truyện rồi đặt tỉ lệ
  cảnh đúng nội dung; truyện thiên thoại → ít combat, lấy đa dạng từ góc máy/nhóm
  nhân vật có thật/chi tiết vật phẩm/thời tiết. Dùng khi muốn hình khớp 100% lời kể.

> Hai cổng tự động (plan gate + depth gate) loại cảnh trùng lặp liền kề, synopsis
> vụn, và block prompt nông (thiếu header / sai độ dài / video >3800 ký tự) rồi tự
> regen có giới hạn — chạy ở cả hai chế độ.

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
3. Copy 1 khối giữa 2 dòng `--- LOOP i / N — Chương X-Y — mood: ... ---`
   (chỉ copy phần prompt tiếng Anh + dòng Negative + dòng Loop, KHÔNG copy dòng
   nhãn `--- LOOP ... ---`)
4. Paste → Lyria tạo đoạn nhạc ~2-3 phút, loop được

**Bao nhiêu loop?** Mặc định 4 (tự co giãn 3–5). Truyện dài / nhiều cao trào →
dùng `--music 5` hoặc hơn. Truyện ngắn / cảm xúc phẳng → `--music 3`.

**Đặt nhạc vào timeline:** mỗi loop có nhãn `Chương X-Y` → đặt đoạn nhạc đó vào
khoảng video tương ứng với các chương đó. **Sync thủ công** — skill không tự
canh timeline.

**Lưu ý giới hạn Lyria:** prompt đã ép instrumental + dòng negative
(`no vocals, no lyrics, ...`), nhưng Lyria VẪN có thể thỉnh thoảng tạo pad nghe
giống giọng người. Đây là giới hạn của model, không loại bỏ 100% được. Nếu đoạn
nào lẫn tiếng hát → re-generate hoặc chỉnh lại mood trong prompt.

**Lưu ý resume nhạc:** khác với scene (có `scene-plan.md` cố định), việc chia
vùng cảm xúc do LLM suy lại mỗi lần chạy, không lưu cố định. Chạy lại có thể
regen loop nhạc nếu ranh giới vùng đổi. Muốn gen sạch → dùng `--force-redo`.

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
Bible lưu mô tả chi tiết, **paste nguyên văn** vào mỗi prompt Subject section.

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
A: Check prompt body ≤900 từ + ≤3 beats + tổng ≤8.0s. Hard cap của skill là 900,
nhưng nếu tool cụ thể vẫn truncate thì trim `Context` trước.

**Q: Có thiếu FAQ — báo ở đâu?**
A: Open issue tại GitHub repo (link trong README.md).
