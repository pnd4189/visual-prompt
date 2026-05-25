# Genre Keywords — VN ↔ EN Visual Vocab

> Related: [[visual-prompt-template]] · [[identity-anchor-rules]] · [[negative-lists]]

Maps Vietnamese xianxia/wuxia trigger words to English visual descriptions
the image/video models understand. Use these to translate scene tags
(extracted from the novel) into the `Setting`, `Subject`, `Style`, and
`Context` sections of prompts.

**Supported genres:** tiên hiệp, huyền huyễn, đô thị, cổ điển, võ hiệp.
**Blocked:** đam mỹ, ngôn tình.

---

## 1. Tiên Hiệp (Xianxia — cultivation, immortal sects)

| VN trigger | EN visual translation |
|---|---|
| tu tiên / luyện khí | seated lotus meditation, qi flowing through dantian, faint blue aura |
| đan dược / luyện đan | bronze pill cauldron, swirling colored smoke, jade vials, herb bundles |
| linh thạch | glowing crystal stones, faint pulsing light, embedded in jade trays |
| pháp bảo | floating ancient artifact, runic inscriptions, soft golden glow |
| phi kiếm | airborne flying sword, trailing silver streak, ribbon of qi |
| nguyên anh | tiny translucent humanoid soul inside dantian, blue-white glow |
| tông môn | mountain-top sect compound, terraced halls, red wood pillars, tile roofs |
| thiên kiếp | lightning storm, sky cracked open, purple-black clouds, descending bolt |
| cảnh giới | floating cultivation stage, glowing meridians visible, energy aura |
| đại đạo | infinite cosmic vista, swirling stars, dao symbol faintly etched in sky |

**Style anchor:** Crouching Tiger Hidden Dragon (2000), Ashes of Time (1994).

---

## 2. Huyền Huyễn (Xuanhuan — mythic fantasy, mixed magic)

| VN trigger | EN visual translation |
|---|---|
| ma pháp / phù chú | glowing runic talisman paper, calligraphy in red ink, faint smoke |
| yêu thú | mythic beast — qilin, nine-tailed fox, jade dragon (Chinese long, NO wings) |
| tà ma | dark-aura demonic entity, shadow tendrils, red glowing eyes |
| thần khí | divine weapon, golden filigree, ancient inscriptions, halo aura |
| huyết mạch | bloodline awakening, eyes shifting color, body glowing |
| đại lục | vast continent map, mountain ranges, hand-painted ink style |
| thượng cổ | primordial era ruins, weathered stone gates, overgrown jade temples |
| thần ma | godlike entity, towering silhouette, robes flowing in cosmic wind |

**Style anchor:** Crouching Tiger Hidden Dragon, Hero (2002).

---

## 3. Đô Thị (Urban — modern setting with cultivation/powers)

| VN trigger | EN visual translation |
|---|---|
| đô thị | modern Chinese city, neon-lit streets, glass skyscrapers, Tang+modern mix |
| công ty | corporate office tower, glass facade, marble lobby |
| đại học | university campus, modern Chinese architecture |
| xe hơi | luxury sedan, polished black, urban backdrop |
| điện thoại | smartphone, hand-held, modern attire |
| ẩn tu | hidden cultivator in modern clothes (suit + jade pendant) |
| võ đường | modern martial arts dojo, wood floors, weapon racks |

**Style anchor:** Wong Kar-wai modern aesthetic (Chungking Express 1994 color),
NOT xianxia robes unless flashback.

---

## 4. Cổ Điển (Gu Dian — historical court, no magic)

| VN trigger | EN visual translation |
|---|---|
| hoàng cung | imperial palace, vermillion pillars, gilded roof tiles, jade staircases |
| triều đình | imperial court, ministers in formal robes, ceremonial drums |
| công chúa | princess, layered silk robes, elaborate hair ornaments, jade circlet |
| tướng quân | general, lamellar armor (NOT European plate), horse-tail helmet, sword |
| chiến trận | battlefield, banners, formations of soldiers, dust clouds, no magic |
| thi thư | scholar's study, scrolls, ink stones, calligraphy brushes, lantern light |
| cổ trang | period costume Tang/Song/Ming, silk and brocade, traditional cuts |

**Style anchor:** Hero (2002), House of Flying Daggers (2004), Curse of the Golden Flower (2006).

---

## 5. Võ Hiệp (Wuxia — jianghu, martial chivalry, NO immortality cultivation)

| VN trigger | EN visual translation |
|---|---|
| võ lâm / giang hồ | wandering swordsman world, inns, bamboo groves, mountain passes |
| khinh công | airborne leap, robes flowing, defying gravity briefly (no flight) |
| nội công | internal energy strike, faint shimmer around fist or palm |
| đao kiếm | jian (straight sword) OR dao (curved saber), lacquered sheath, silk tassel |
| khách điếm | rural Chinese inn, wooden tables, paper lanterns, traveling guests |
| trúc lâm | bamboo forest, dappled green light, mist between stalks |
| tửu lâu | two-story wooden tavern, balcony, hanging lanterns |
| môn phái | martial sect compound, courtyards, training fields |

**Style anchor:** Hero (2002), Crouching Tiger Hidden Dragon (2000).
Key diff vs tiên hiệp: NO magical formations, NO flying swords, NO qi auras
beyond subtle palm shimmer. Power expressed through choreography, not VFX.

---

## 6. Đam Mỹ / Ngôn Tình — **BLOCKED**

This skill **refuses** đam mỹ (BL romance) and ngôn tình (modern romance)
input. The `genre-detector.md` prompt halts the workflow with a Vietnamese
refusal message when these keywords dominate.

Refusal trigger keywords (any 2+ → halt):
- đam mỹ, BL, công thụ, chủ công, chủ thụ, công x thụ, thụ x công
- ngôn tình, tổng tài, đại thiếu gia, bá đạo tổng tài, ngược luyến, ngọt sủng
- (also any explicit romantic/sexual content beyond proofread-level)

Refusal message (Vietnamese):
> "Skill này chỉ hỗ trợ tiên hiệp / huyền huyễn / đô thị / cổ điển / võ hiệp.
> Thể loại đam mỹ / ngôn tình ngoài phạm vi hiện tại. Workflow đã dừng."
