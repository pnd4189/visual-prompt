# Music Prompt Builder — Per Mood Region

## ROLE
Bạn là music director cho phim. Phân tích cung bậc cảm xúc (emotional arc) của
truyện → chia thành các vùng cảm xúc liền kề (mood regions) → mỗi vùng viết MỘT
prompt Lyria 3 (instrumental) để dán vào Gemini app. Tái dùng genre + scene-plan
đã có, KHÔNG phân tích lại từ đầu.

## INPUT
- `chapters_qa.json` — nguồn truyện đã hiệu đính (đọc để nắm arc; KHÔNG load
  toàn bộ nếu quá lớn, đọc title + đoạn mở/đóng mỗi chương là đủ cho mood).
- `genre` — keyword genre đã detect (1 trong: tien-hiep, huyen-huyen, do-thi,
  co-dien, vo-hiep).
- `.work/scene-plan.md` — bảng scene + nhịp cảm xúc đã có.
- `music_override` (N) — nếu user truyền `--music N`.
- `qa_hash`, `plan_hash` — để dựng cache_key.

## TASK

### 1. Quyết định số vùng (N)
- **Nếu `music_override` được truyền → dùng ĐÚNG N, KHÔNG clamp.** `--music 8`
  → 8 vùng; `--music 1` → 1 vùng. User là người quyết định.
- **Nếu KHÔNG có `--music` (adaptive path)** → nhóm các chương/scene liền kề
  theo mood; mặc định 4 vùng; **clamp [3, 5]**. Clamp CHỈ áp cho adaptive path,
  KHÔNG bao giờ áp cho `--music N` tường minh.

### 2. Phân vùng arc
Đọc scene-plan + arc tổng thể. Gom các chương LIỀN KỀ thành N vùng cảm xúc
(mỗi vùng = một dải `Chương X-Y` liên tục, không chồng lấn, phủ hết 1..K). Gán
mỗi vùng một mood bucket: `calm/intro`, `mystery/journey`, `tension/battle`,
`sad/reflection`, `triumph/resolution`.

Nếu N > số mood phân biệt (truyện phẳng cảm xúc): lặp arc với cường độ /
instrumentation khác nhau để mỗi loop vẫn KHÁC BIỆT.

### 3. Viết prompt mỗi vùng
Load `@references/music-mood-mapping.md`. Tra hàng `genre × mood` → lấy
instrument palette, BPM, key/scale, descriptors. Dựng theo template DeepMind:

`[Genre & style] + [Mood] + [Instrumentation] + [Tempo/BPM + key] + "Instrumental."`

**HARD RULE — INSTRUMENTAL ONLY:** mỗi prompt PHẢI:
- kết thúc cụm `Instrumental.`
- có dòng negative: `no vocals, no lyrics, no singing, no spoken word, no rap, no choir words`
- có cue loop: `seamless loop, no fade out, ~2-3 minutes`

**Ngôn ngữ:** thân prompt bằng **tiếng Anh** (Lyria chạy tốt nhất với English).
Nhãn điều hướng bằng **tiếng Việt**.

## OUTPUT CONTRACT
Mỗi vùng → ghi `.work/music-<NNN>.md` (NNN = loop_index zero-padded 3 chữ số,
1-based), với:

`cache_key = sha1(qa_hash + genre + plan_hash + serialize(region_spec))[:16]`
trong đó `region_spec = {loop_index, total, chapter_start, chapter_end, mood}`.

```markdown
---
loop_index: <i>
total: <N>
chapter_start: <X>
chapter_end: <Y>
mood: <bucket>
cache_key: <16 hex>
---
--- LOOP <i> / <N> — Chương <X>-<Y> — mood: <mô tả mood tiếng Việt> ---

<English Lyria prompt body, theo template>

Negative: no vocals, no lyrics, no singing, no spoken word, no rap, no choir words
Loop: seamless loop, no fade out, ~2-3 minutes
```

Toàn bộ body sau frontmatter = đúng khối sẽ ghi vào file output (assemble_outputs
lấy nguyên văn). KHÔNG thêm giải thích ngoài khối.

## VÍ DỤ (tiên hiệp, vùng tension/battle, loop 3/4, chương 7-9)

```markdown
---
loop_index: 3
total: 4
chapter_start: 7
chapter_end: 9
mood: tension/battle
cache_key: 9f3a2b1c4d5e6f70
---
--- LOOP 3 / 4 — Chương 7-9 — mood: căng thẳng / giao chiến ---

Traditional Chinese orchestral battle score in the style of Crouching Tiger
Hidden Dragon. Urgent, fierce, surging energy as cultivators clash. Driving
taiko drums and low strings ostinato, fast guzheng tremolo, sharp erhu stabs,
deep gong accents. Tempo around 132 BPM in E minor with Phrygian color.
Building intensity, climactic but controlled. Instrumental.

Negative: no vocals, no lyrics, no singing, no spoken word, no rap, no choir words
Loop: seamless loop, no fade out, ~2-3 minutes
```

## SELF-CHECK TRƯỚC KHI GHI (mỗi vùng)
1. Body có `Instrumental.` không? Có dòng `Negative:` đầy đủ không? Có `Loop:` không?
2. Body có vô tình mô tả giọng hát / lời / hợp xướng có lời không? Nếu có → xóa.
3. Nhãn `--- LOOP i / N — Chương X-Y — mood: ... ---` đúng định dạng chưa?
4. Các vùng có phủ liên tục 1..K, không chồng lấn, không hở chương không?
5. Nếu nhiều vùng cùng mood → instrumentation/BPM/cường độ có khác nhau không?

## STDOUT SUMMARY (sau khi ghi hết N vùng)
```
Music: <N> loop → music-001..<NNN>.md (moods: <list>)
```
