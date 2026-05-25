# Scene Planner — Pass 1

## ROLE
Read the entire novel + bible + genre → produce a flat ordered list of N
distinct scenes covering the full narrative arc, with M of them flagged for
video expansion.

## INPUT
- `chapters` — full JSON list
- `bible` — `character-bible.md` content
- `genre` — detected genre keyword
- `images_n` — total image count target (e.g., 45)
- `videos_m` — total video count target (e.g., 6)

## TASK
1. Read all chapters in order. Identify the narrative arc: setup, rising
   action, climax(es), resolution.
2. Allocate ~N scenes proportionally across the arc:
   - Establishing scenes (first chapter, new locations): wide shots
   - Action / climax scenes: motion shots
   - Dialogue / emotional: close-ups
   - Travel / transition: lateral tracking
3. For each scene, fill: scene_id, chapter_ref, scene_tag, characters_present,
   synopsis_1line, flag_for_video.
4. **Flag exactly M scenes** for video. Pick from: openers, climaxes,
   action-dense, ritual reveals, big travel montages. NEVER flag pure
   dialogue or static meditation.
5. Distribute scenes ROUGHLY evenly across chapters (don't dump 30 scenes
   into chapter 1 and 2 into chapter 10).

## SCENE TAGS (must be one of)
`establishing`, `action`, `dialogue`, `reveal`, `emotional`, `ritual`, `travel`

(Maps to camera defaults via `@references/scene-tag-camera-mapping.md`.)

## OUTPUT
Write `.work/scene-plan.md`:

```markdown
# Scene Plan — <input filename>

Genre: <genre> · Images: <N> · Videos: <M> · Chapters: <K>

| scene_id | chapter | scene_tag | characters | synopsis | video? |
|---|---|---|---|---|---|
| 001 | 1 | establishing | Trương Tiểu Phàm | Tiểu Phàm đứng trên đỉnh Linh Sơn, gió thổi, kiếm trong tay | ✓ |
| 002 | 1 | dialogue | Trương Tiểu Phàm, Phổ Hồng | Phổ Hồng hỏi Tiểu Phàm đã sẵn sàng xuống núi chưa | |
| 003 | 2 | travel | Trương Tiểu Phàm | Đi qua thác nước, rừng trúc khi mặt trời lặn | |
| ... | ... | ... | ... | ... | ... |
```

## UNIQUENESS SELF-CHECK (mandatory before write)

Scan your own table. For every pair of scenes within 5 indices of each other:
- If they share >70% of characters AND same scene_tag AND similar location/
  setting → REVISE one of them (change scene_tag, change focus character, OR
  drop and reuse the index for a different moment).

Repeat until 0 near-duplicate pairs remain.

## DISTRIBUTION CHECK

- Total scenes = `images_n` (exact).
- Video-flagged scenes = `videos_m` (exact).
- Per-chapter scene count: `images_n / chapters` ± 30% tolerance.

If any check fails → revise before writing the file.

## STDOUT SUMMARY
```
Scene plan written: .work/scene-plan.md
Total scenes: <N> (<M> flagged for video)
Video indices: <comma-sep list>
Chapters covered: 1..<K>
```
