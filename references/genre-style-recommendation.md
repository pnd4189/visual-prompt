# Genre → Style Recommendation (soft)

> Related: [[style-catalog]] · [[genre-keywords]]

**Soft recommendation only.** Genre and style are fully decoupled — *any* of the 18
styles in [[style-catalog]] is valid for *any* genre. This table just suggests a
sensible default (#1) plus alternatives per genre. The user always decides; `--style`
overrides everything.

Genre keys match the detector / `--genre` flag: `tien-hiep`, `huyen-huyen`,
`do-thi`, `co-dien`, `vo-hiep`.

---

## Recommendation table

| Genre | #1 (default) | Alternatives | Why |
|---|---|---|---|
| **tiên hiệp** (`tien-hiep`) | `donghua-xianxia` | `painterly-realism-cinematic`, `game-cg-25d`, `ink-wash-stylized` | Cultivation worlds read best in modern 3D donghua; cinematic for a grounded look, game-CG for vivid sects, ink-wash for title cards. |
| **huyền huyễn** (`huyen-huyen`) | `dark-fantasy-modao` | `game-cg-25d`, `concept-art-cityscape`, `donghua-xianxia` | Mythic/demonic fantasy suits a brooding hybrid look; CG and concept-art carry scale and spectacle. |
| **đô thị** (`do-thi`) | `semi-realistic-digital-painting` | `manhua`, `scifi-donghua-kehuan` | Modern settings favor semi-real painting; manhua for lighter tone, sci-fi for tech/near-future. |
| **cổ điển** (`co-dien`) | `painterly-realism-cinematic` | `watercolor-gouache`, `ink-wash-stylized` | Historical court drama matches cinematic realism; watercolor/ink-wash for elegant accents. |
| **võ hiệp** (`vo-hiep`) | `painterly-realism-cinematic` | `ink-wash-stylized`, `manhua` | Wuxia choreography shines in cinematic realism; ink-wash for poetic moments, manhua for action panels. |

---

## Notes for the recommender

- Always present #1 first, then 2-3 alternatives from the row above.
- If the chosen/recommended style is **accent-title-card** or **video-oriented**
  (see category in [[style-catalog]]), warn: it keeps character identity poorly across
  many scenes — best for opening title cards or montages, not every shot.
- Alternatives are suggestions, not limits: the user may type any valid id from the
  catalog's quick-reference table.
