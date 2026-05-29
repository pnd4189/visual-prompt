# Style Recommender — Per Run

## ROLE
After genre is detected, recommend an art style for the whole run. Output a #1
default + 2-3 alternatives + a consistency warning when relevant. You do NOT pick the
final style — STEP 3.5 in the command asks the user; you only inform that choice.

## INPUT
- `genre` — detected genre key (one of: `tien-hiep`, `huyen-huyen`, `do-thi`,
  `co-dien`, `vo-hiep`).
- optional `sample` — a short excerpt of the QA'd text for tone (optional; use only
  if it clearly nudges the recommendation, e.g. very dark vs. light tone).

## TASK
1. Load `@references/genre-style-recommendation.md` — find the row for `genre`.
   Its #1 is the default; its alternatives are the suggested others.
2. Load `@references/style-catalog.md` — for each style you list, read its
   `category`, one-line description, and `identity consistency`.
3. If #1 or any listed style is `accent-title-card` or `video-oriented`, add the
   consistency warning (see OUTPUT). The default #1 per genre is always narrative-safe,
   so the warning usually applies only to alternatives.
4. Keep it short. This is a console prompt the user reads before choosing.

## OUTPUT (print to console, Vietnamese labels)

```
Gợi ý style cho thể loại <genre>:

  ➤ #1 (mặc định): <id> — <one-line VN/EN desc> [<category>]
  Lựa chọn khác:
    - <id> — <desc> [<category>]
    - <id> — <desc> [<category>]
    - <id> — <desc> [<category>]

<Nếu có style accent/video trong danh sách:>
  ⚠ Lưu ý: <id(s)> thuộc nhóm accent-title-card/video — giữ nhất quán nhân vật
    kém qua nhiều scene; hợp cho title card / montage hơn là mọi cảnh.

Nhấn Enter để dùng #1 (<id>), hoặc gõ một id khác (xem references/style-catalog.md).
```

## RULES
- Recommend ONLY ids that exist in `style-catalog.md` quick-reference.
- #1 must equal the genre's #1 in `genre-style-recommendation.md` unless `sample`
  gives a strong tonal reason to promote an alternative — if you do, say why in one
  clause.
- Never invent ids. Never recommend a blocked genre.
