# 🔍 Image Prompt Quality Review — Bình Thiên Sách (Ch.201–300)

**Reviewer**: Opus Review Pipeline  
**Date**: 2026-06-27  
**Scope**: 10 files × ~150 scenes = ~1,499 image prompts  
**Expected format**: 10 sections/scene (Camera, Story DNA, Setting, Composition, Subject, Action/Energy, Style, Lighting/Color, Atmosphere, Negative)

---

## 📊 Bảng Tóm Tắt

| # | File | Scenes | Lines | Size | CN Leak | "None" bug | "build build / hair hair" | Sections | Unique StoryDNA | Rating |
|---|------|--------|-------|------|---------|------------|---------------------------|----------|-----------------|--------|
| 1 | `0201_0210` | 149 ⚠️ | 3,276 | 626KB | ✅ 0 | 🔴 52 | 🔴 90 | 10/10 | 149/149 | 🔴 **ISSUE** |
| 2 | `0211_0220` | 150 | 3,298 | 397KB | ✅ 0 | 🔴 96 | 🟡 4 | 10/10 | 30/150 ⚠️ | ⚠️ **MINOR** |
| 3 | `0221_0230` | 150 | 3,320 | 425KB | ✅ 0 | 🟡 9 | ✅ 0 | 10/10 | 149/150 | ✅ **PASS** |
| 4 | `0231_0240` | 150 | 3,303 | 390KB | ✅ 0 | ✅ 0 | 🟡 1 | 10/10 | 150/150 | ✅ **PASS** |
| 5 | `0241_0250` | 150 | 3,298 | 400KB | ✅ 0 | ✅ 0 | ✅ 0 | 10/10 | 122/150 ⚠️ | ⚠️ **MINOR** |
| 6 | `0251_0260` | 150 | 3,357 | 405KB | ✅ 0 | ✅ 0 | 🟡 2 | 10/10* | 150/150 | ✅ **PASS** |
| 7 | `0261_0270` | 150 | 3,329 | 394KB | 🟡 5 | ✅ 0 | ✅ 0 | 10/10 | 150/150 | ⚠️ **MINOR** |
| 8 | `0271_0280` | 150 | 3,381 | 407KB | ✅ 0 | 🟡 3 | 🟡 22 | 10/10 | 150/150 | ⚠️ **MINOR** |
| 9 | `0281_0290` | 150 | 2,098 | 241KB | ✅ 0 | 🔴 62 | ✅ 0 | ❌ 7/10 | 150/150 | 🔴 **ISSUE** |
| 10 | `0291_0300` | 150 | 3,298 | 430KB | ✅ 0 | 🟡 25 | ✅ 0 | 10/10 | 150/150 | ✅ **PASS** |

> **Lưu ý**: Video prompts nằm trong file riêng `*_video_prompts.txt`, KHÔNG nằm trong `*_image_prompts.txt`. Các file 2, 7, 8, 9 không có file `_video_prompts.txt` tương ứng (video bypass) — đúng như expected.

---

## 🔴 CHI TIẾT VẤN ĐỀ

### File 1: `0201_0210` — 🔴 ISSUE (Cần regenerate)

**Vấn đề chính: Template cũ (v1), boilerplate nặng**

| Vấn đề | Mức độ | Chi tiết |
|--------|--------|----------|
| Thiếu 1 scene | ⚠️ | Chỉ 149 scenes thay vì 150 |
| Boilerplate filler | 🔴 | Mỗi section kết thúc bằng cùng 1 câu generic lặp lại (vd: Camera → "This cinematography is specifically chosen to maximize..."; Story DNA → "The narrative arc of this moment captures the essential spirit...") |
| Camera chỉ 4 variant | 🔴 | 149 scenes chỉ dùng 4 camera descriptions, xoay vòng |
| Setting chỉ 5 variant | 🔴 | Không gắn với nội dung thực |
| Style 100% copy-paste | 🔴 | Tất cả 149 scenes dùng đúng 1 dòng Style |
| Subject cycling | 🔴 | Chỉ 20 cặp nhân vật unique, lặp theo chu kỳ |
| `"None"` trong Subject | 🔴 | 52 scenes có literal "None" thay cho accessories (vd: "weary but determined eyes, None, wearing...") |
| `"build build"`, `"hair hair"` | 🔴 | 90 lỗi template duplication (vd: "muscular imposing build build", "long black hair hair") |

**Verdict**: Cần **regenerate hoàn toàn** bằng pipeline mới.

---

### File 2: `0211_0220` — ⚠️ MINOR

| Vấn đề | Mức độ | Chi tiết |
|--------|--------|----------|
| Story DNA chỉ 30/150 unique | ⚠️ | 89 scenes dùng cùng 1 Story DNA ("late-dynasty cultivation era, analyzing the battlefield clues..."), 33 scenes dùng 1 cái khác |
| Camera chỉ 30 variant | ⚠️ | 89 scenes dùng cùng 1 camera shot |
| `"None"` trong Subject | 🔴 | 96 scenes — nhiều nhất trong tất cả files |
| "build build" / "hair hair" | 🟡 | 4 lỗi |

**Verdict**: Chất lượng tổng thể khá (format v2), nhưng Story DNA + Camera lặp nhiều. Có thể ship nếu "None" được clean.

---

### File 3: `0221_0230` — ✅ PASS

- Format hybrid v2→v3 (scenes đầu lens-based, scenes sau bracket-based) — cả hai đều chất lượng tốt
- 149/150 Story DNA unique, 150/150 Subject unique
- Chỉ 9 lỗi "None" nhỏ
- **Ship được**

---

### File 4: `0231_0240` — ✅ PASS

- Format v2 ổn định, 150/150 Story DNA unique, 150/150 Subject unique
- Ngụy Quan Tinh có VN trong Subject field ("lôi thôi lếch thếch build, bù xù như cỏ dại") — cosmetic nhưng có thể ảnh hưởng image generation
- 1 lỗi "build build" nhỏ
- **Ship được**

---

### File 5: `0241_0250` — ⚠️ MINOR

| Vấn đề | Mức độ | Chi tiết |
|--------|--------|----------|
| Story DNA 122/150 unique | 🟡 | 28 scenes trùng (6 groups × ~4-6 lần) |
| Negative prompt lỗi | 🔴 | **101 scenes** (2/3 file!) có Negative bị hỏng: "modestly clothed, modestly clothed, excessive no graphic blood, no graphic blood" — template garbled |
| Format inconsistent | 🟡 | v2 → v3 transition mid-file |

**Verdict**: Negative prompt cần fix (sed replace) trước khi ship.

---

### File 6: `0251_0260` — ✅ PASS

- 150 scenes, chất lượng cao, 150/150 unique StoryDNA + 141/150 unique Subject
- Format `**Negative:**` (bold markdown) ở 5 scenes cuối thay vì `Negative:` — cosmetic only, nhưng nên normalize
- 2 lỗi "build build" nhỏ
- **Ship được**

---

### File 7: `0261_0270` — ⚠️ MINOR

| Vấn đề | Mức độ | Chi tiết |
|--------|--------|----------|
| Chinese char leak | 🟡 | 5 dòng chứa `策` ("Iron策 Army" thay vì "Thiết Sách Army"): lines 137, 143, 161, 181, 203 |

**Fix**: `sed -i 's/Iron策/Thiết Sách/g' file` — 1 lệnh, xong.

---

### File 8: `0271_0280` — ⚠️ MINOR

| Vấn đề | Mức độ | Chi tiết |
|--------|--------|----------|
| "build build" / "hair hair" | 🟡 | 22 lỗi — chủ yếu scenes 1-140 |
| VN trong Story DNA | 🟡 | 42 scenes có Story DNA tiếng Việt thay vì tiếng Anh |
| Scenes 141-150 format khác | 🟡 | Negative block format khác, Story DNA tiếng Việt — pipeline transition |
| "None" trong Subject | 🟡 | 3 scenes |

**Verdict**: Chấp nhận được, "build build" nên sed-fix.

---

### File 9: `0281_0290` — 🔴 ISSUE (Cần regenerate)

**Vấn đề chính: Pipeline hoàn toàn khác, chất lượng cực thấp**

| Vấn đề | Mức độ | Chi tiết |
|--------|--------|----------|
| Style **TRỐNG** | 🔴🔴 | Toàn bộ 150 scenes: `Style: ` (empty). Thiếu hoàn toàn style descriptor "high-end Chinese 3D cultivation donghua render..." |
| Camera = 1 variant | 🔴🔴 | 150 scenes dùng ĐÚNG 1 câu: "Highly detailed and meticulously framed cinematic shot, capturing the essence of the moment." |
| Setting = 1 variant | 🔴🔴 | 150 scenes: "Vast and immersive environment matching the mood of the scene." |
| Composition = 1 variant | 🔴🔴 | 150 scenes: "The frame is masterfully balanced with deep multi-layered depth; subjects are placed prominently." |
| Atmosphere SPAM | 🔴 | Lặp lại "masterpiece epic stunning beautiful cinematic highly-detailed 8k trending vivid" — token stuffing, giảm dần quality keywords |
| Story DNA + Action = VN | ⚠️ | Toàn bộ bằng tiếng Việt thay vì tiếng Anh |
| Negative generic | 🔴 | Dùng "low resolution, blurry, distorted..." thay vì anti-Western/anti-IP negative chuẩn |
| "None" trong Subject | 🔴 | 62 scenes |
| File ngắn bất thường | ⚠️ | 2,098 dòng (vs ~3,300 trung bình) — do content mỏng |

**Verdict**: **PHẢI TẠO LẠI HOÀN TOÀN**. File này sinh bởi pipeline khác (có vẻ fallback/legacy), không đạt tiêu chuẩn.

---

### File 10: `0291_0300` — ✅ PASS

- 150 scenes, chất lượng cao, 150/150 unique StoryDNA + Subject
- 25 lỗi "None" nhỏ trong Subject
- Negative format có 2 variant (cả hai hợp lệ)
- **Ship được**

---

## 🎯 VERDICT TỔNG

### ❌ CHƯA SHIP ĐƯỢC — Cần fix 2 file + sed-fix 3 file

| Hành động | File | Chi tiết |
|-----------|------|----------|
| 🔴 **REGENERATE** | File 1 (`0201_0210`) | Template v1 cũ, boilerplate 100%, "build build"/"hair hair", cycling subjects |
| 🔴 **REGENERATE** | File 9 (`0281_0290`) | Style trống, Camera/Setting/Comp = 1 variant, Atmosphere spam, pipeline hoàn toàn sai |
| 🟡 **SED-FIX** | File 5 (`0241_0250`) | Negative prompt garbled ở 101 scenes — fix bằng sed replace |
| 🟡 **SED-FIX** | File 7 (`0261_0270`) | 5 chỗ `Iron策` → `Thiết Sách` |
| 🟡 **SED-FIX** | File 8 (`0271_0280`) | 22 lỗi "build build"/"hair hair" — `sed -i 's/ build build/ build/g; s/ hair hair/ hair/g'` |
| 🟢 **CLEAN** (optional) | Files 1,2,3,8,9,10 | Remove literal "None" trong Subject descriptions |

### Sau khi fix:
- ✅ Ship-ready: Files 2, 3, 4, 5*, 6, 7*, 8*, 10
- 🔴 Cần regenerate: Files **1**, **9**

---

## 📝 Lỗi hệ thống xuyên suốt (Root Cause)

1. **`"None"` literal trong Subject**: 247 lần tổng cộng (6/10 files). Pipeline inject "None" khi character thiếu accessories/distinguishing features. → **Sửa template gốc** để output empty string hoặc bỏ qua field.

2. **`"build build"`, `"hair hair"` duplication**: 119 lần (5/10 files). Template nối "build" + build_type → "muscular build build". → **Sửa template nối chuỗi**.

3. **Format inconsistency**: Ít nhất 3 pipeline version (v1=generic boilerplate, v2=lens-based detailed, v3=bracket notation). Files 3, 5 chuyển format giữa chừng. → **Standardize trên 1 pipeline version**.

4. **VN trong EN fields**: Story DNA, Subject, Action/Energy đôi khi dùng tiếng Việt thay vì tiếng Anh. → Có thể ảnh hưởng image generation quality nếu model chỉ hiểu EN.
