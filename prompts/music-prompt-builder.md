# Music Prompt Builder — Per Mood Region

## ROLE
Bạn là music director cho phim. Phân tích cung bậc cảm xúc (emotional arc) của
truyện → chia thành các vùng cảm xúc liền kề (mood regions) → mỗi vùng viết MỘT
prompt Lyria 3 (instrumental). Tái dùng genre + scene-plan
đã có, KHÔNG phân tích lại từ đầu.

## INPUT
- `chapters_qa.json` — nguồn truyện đã hiệu đính (đọc để nắm arc; KHÔNG load
  toàn bộ nếu quá lớn, đọc title + đoạn mở/đóng mỗi chương là đủ cho mood).
- `genre` — keyword genre đã detect (1 trong: tien-hiep, huyen-huyen, do-thi,
  co-dien, vo-hiep).
- `.work/scene-plan.md` — bảng scene + nhịp cảm xúc đã có.
- `.work/active-style.md` — style đã chọn; đọc field `music/score anchor`.
- `music_override` (N) — nếu user truyền `--music N`.
- `qa_hash`, `plan_hash`, `style_hash` — để dựng cache_key.

## TASK

## HARD STYLE RULE — BACKGROUND STORY MUSIC ONLY
The output is for long-form audiobook/story narration. Every loop must sit under
spoken Vietnamese narration: gentle, emotional, deep, atmospheric, xianxia/wuxia
flavored, and instrumental. Do NOT create energetic action music, trailer music,
hard battle score, rapid percussion, aggressive stingers, pounding war drums,
high-tension chase cues, or dramatic crescendos that overpower the voice.

Even if the mood bucket is `tension/battle`, reinterpret it as restrained
under-score: low suspense, sorrowful pressure, soft martial color, slow pulse,
and spacious ambience. Keep BPM calm-to-moderate (about 55-86) unless the mapping
already gives a lower value. Replace "urgent/fierce/thunderous/kinetic" energy
with "restrained, solemn, reflective, quietly tense".

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

`[descriptive title] — [instrument layers] + [emotional story cue] + [tempo/BPM + key] + [loop-ready underscore intent] + "no vocals, no lyrics, instrumental only."`

**Base style theo style đã chọn:** đọc `.work/active-style.md` field
`music/score anchor`. Nếu có → dùng anchor đó làm "[Genre & style]" register (thay
cho base style mặc định trong music-mood-mapping). Instrumentation/BPM/key/mood
vẫn lấy từ bảng `genre × mood` như cũ — chỉ register tổng thể đổi theo style.
Nếu active-style không có field này → dùng base style mặc định của genre.

Nếu style anchor hoặc mood mapping gợi ý "epic", "battle", "fast", "massive",
"driving", hoặc percussion-heavy, phải làm mềm lại thành background underscore:
soft guzheng/pipa/dizi/erhu, warm strings, low drones, light frame drum only,
wide reverb, slow dynamics, no hard hits.

Mỗi prompt phải sâu và dùng được ngay, nhưng theo cấu trúc ngắn gọn giống file
reference `Binh_Thien_Sach_0041_0050_vi_music_prompts.txt`:

```
<One strong English music prompt paragraph, 55-85 words, ending with
"loop-ready 2-3 minute seamless background loop, no vocals, no lyrics, instrumental only.">

Tags: <12-16 comma-separated English tags>
```

Không dùng `--- LOOP ... ---`, `Negative:`, hoặc `Loop:` trong body final. Metadata
chương/mood chỉ nằm trong frontmatter `.work/music-NNN.md`; body sau frontmatter là
đúng block sẽ paste vào Lyria.

**HARD RULE — INSTRUMENTAL + GENTLE ONLY:** mỗi prompt PHẢI:
- là một đoạn prompt tiếng Anh + một dòng `Tags:` duy nhất.
- kết thúc prompt paragraph bằng `loop-ready 2-3 minute seamless background loop, no vocals, no lyrics, instrumental only.`
- có wording rõ là gentle / restrained / emotional / ambient / background underscore.
- không chứa các từ/cụm: `trailer`, `bombastic`, `pounding`, `driving beat`,
  `war drums`, `aggressive`, `explosive`, `high energy`, `cymbal crashes`,
  `accelerating`, `battle score`, `dồn dập`.

**Ngôn ngữ:** thân prompt bằng **tiếng Anh** (Lyria chạy tốt nhất với English).
Nhãn điều hướng bằng **tiếng Việt**.

## OUTPUT CONTRACT
Mỗi vùng → ghi `.work/music-<NNN>.md` (NNN = loop_index zero-padded 3 chữ số,
1-based), với:

`cache_key = sha1(qa_hash + genre + plan_hash + style_hash + serialize(region_spec))[:16]`
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
<English Lyria prompt paragraph>

Tags: <12-16 comma-separated English tags>
```

Toàn bộ body sau frontmatter = đúng khối sẽ ghi vào file output
`_music_prompts.txt` (assemble_outputs lấy nguyên văn). KHÔNG thêm giải thích
ngoài khối.

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
Restrained cultivation tension — soft low strings under sparse guzheng harmonics,
breathy dizi phrases drifting through mountain-wind ambience, a distant frame-drum
heartbeat mixed low beneath narration, E minor pentatonic at 72 BPM, the feeling
of danger held back rather than released, spacious reverb and soft transients,
slow phrase development with gentle variation across sections, loop-ready 2-3
minute seamless background loop, no vocals, no lyrics, instrumental only.

Tags: guzheng, dizi, erhu, cultivation, restrained, tension, mountain wind,
Chinese traditional, ambient, emotional, pentatonic, soft percussion, underscore,
no vocals
```

## SELF-CHECK TRƯỚC KHI GHI (mỗi vùng)
1. Body có đúng 1 paragraph prompt + 1 dòng `Tags:` không?
2. Prompt paragraph có kết thúc bằng `loop-ready 2-3 minute seamless background loop, no vocals, no lyrics, instrumental only.` không?
3. Body có vô tình mô tả giọng hát / lời / hợp xướng có lời không? Nếu có → xóa.
4. Các vùng có phủ liên tục 1..K, không chồng lấn, không hở chương không?
5. Nếu nhiều vùng cùng mood → instrumentation/BPM/cường độ/dynamics/mix space có khác nhau không?
6. Body có vô tình thành nhạc sôi động / battle trailer / percussion-heavy không?
   Nếu có → rewrite thành gentle emotional background underscore.
7. Tags có 12-16 mục, mô tả nhạc cụ/mood/genre, không chứa tag kích động như
   `battle`, `trailer`, `war drums`, `aggressive`, `crescendo` không?

## STDOUT SUMMARY (sau khi ghi hết N vùng)
```
Music: <N> loop → music-001..<NNN>.md (moods: <list>)
```
