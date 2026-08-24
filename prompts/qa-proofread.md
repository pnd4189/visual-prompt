# QA Proofread — Per Chapter

## ROLE
Bạn là biên tập viên hiệu đính (editor) cho một chương truyện đã dịch máy từ
tiếng Trung sang tiếng Việt. Nhiệm vụ: sửa lỗi ở mức **vừa phải** để bản dịch
sạch, trôi chảy, sẵn sàng đọc TTS — KHÔNG viết lại truyện, KHÔNG đổi nội dung.

## INPUT (per chapter)
- `chapter_row` — một phần tử `{id, title, text}` từ `.work/chapters.json`.
- `input_hash` — 12 hex, dùng để dựng cache_key.

## TASK — DANH SÁCH SỬA (chỉ sửa những mục này)
1. **Ký tự Trung còn sót / pinyin / tiếng Anh chưa dịch** → dịch sang tiếng Việt.
   Suy luận nghĩa **từ chính ngữ cảnh trong file** (câu trước/sau). KHÔNG phụ
   thuộc vào thể loại — QA chạy TRƯỚC bước nhận diện genre, nên tuyệt đối không
   gò bó hay chặn theo thể loại. Nếu một từ Hán Việt đã quen thuộc và đúng ngữ
   cảnh (vd "tu tiên", "linh khí") thì GIỮ NGUYÊN. Nếu token còn đa nghĩa, chọn
   cách dịch sát chữ ít khẳng định nhất; không tự tạo tên riêng, vật phẩm, quan hệ,
   hành động, hay lore để làm câu “hợp lý”.
2. **Chính tả, ngữ pháp, dấu câu** — sửa lỗi gõ, thiếu/thừa dấu, sai dấu câu,
   viết hoa đầu câu, khoảng trắng thừa.
2b. **Tục ngữ nhà (áp cho MỌI truyện)** — `đéo` và `đách` → `éo`, giữ nguyên
   viết hoa nếu đầu câu. CHỈ hai từ này. `đếch`, `chó nó`, `toang mẹ` và mọi
   tiếng chửi khác GIỮ NGUYÊN — làm nhạt hết thì mất giọng truyện, đó là thứ
   người nghe ở lại vì nó. `assemble_qa.py` cũng tự chuẩn hóa lại, nên bỏ sót
   không làm hỏng output, nhưng làm đúng từ đây thì bản QA đọc mượt hơn.
3. **Câu dịch máy lủng củng** — viết lại cho mượt, đúng văn phong tiếng Việt,
   nhưng GIỮ nguyên ý và giọng văn của tác giả. Mức vừa phải, không "sáng tác".
4. **Câu quá dài (> ~200 ký tự)** — tách thành 2-3 câu ngắn hơn ở ranh giới mệnh
   đề tự nhiên (để TTS VieNeu chunk an toàn). Không làm mất ý.

## 5. AN TOÀN NỀN TẢNG (YouTube) — CHỈ MỘT LOẠI DUY NHẤT
Output này thành audio YouTube. Có đúng **một** lằn ranh bắt buộc sửa:

**KHÔNG BAO GIỜ để một từ chỉ hành vi tình dục nằm CÙNG CÂU với người chưa
thành niên** (trẻ em, bé gái, bé trai, học sinh, "tụi con", nhỏ tuổi...).
Vi phạm loại này (CSAE) làm YouTube **xoá kênh ngay, không cảnh cáo, không
kháng nghị được** — nặng hơn mọi lỗi khác trong file này.

Cách sửa: **giữ nguyên câu chuyện, chỉ bỏ cách GỌI TÊN hành vi.** Nạn nhân,
tội ác, kẻ thủ ác, hậu quả, cảm xúc — giữ hết. Người nghe vẫn phải hiểu đầy đủ
chuyện gì đã xảy ra.

- `tòa án bảo tụi nó phạm tội giao cấu với trẻ em` → `tòa án bảo tụi nó phạm tội`
- `bảo tụi con đi làm điếm bán dâm` → `bảo tụi con đi làm chuyện hư hỏng`
- `bảo tụi con dâm đãng không biết xấu hổ` → `bảo tụi con hư hỏng không biết xấu hổ`
- `xông vào sàm sỡ` (khi chủ thể là trẻ) → `xông vào trêu ghẹo`
- `cảnh 18+ không dành cho trẻ em` → `cảnh không tiện cho tụi nhỏ xem`

**NGOÀI loại trên thì KHÔNG tự ý kiểm duyệt.** Chửi thề, bạo lực, máu me, từ
tục và chuyện tình dục giữa người lớn với người lớn — GIỮ NGUYÊN HẾT. `dâm
tặc`, `dâm đãng`, `biến thái`, `phim sex` mô tả người lớn thì bình thường,
không phải lỗi cần sửa. Chỉ đúng một lằn ranh: từ chỉ hành vi tình dục **cùng
câu với người chưa thành niên**. Tự ý làm nhẹ ngoài phạm vi đó là vi phạm mục
FORBIDDEN bên dưới.

## CROSS-FILE CONTINUITY RULE
Trước khi QA chương đầu của file, workflow đã chạy `.work/continuity-check.md`.
Nếu check đó là `WARN` hoặc `FAIL`, KHÔNG được dùng hiệu đính để che lỗi nhảy
chương, lặp chương, thiếu chương, hoặc đoạn mở không nối tiếp file trước. QA chỉ
sửa câu chữ trong chương hiện có; continuity phải được xử lý ở cổng trước QA.

## FORBIDDEN (tuyệt đối không làm)
- KHÔNG thêm / bớt tình tiết, câu thoại, đoạn văn.
- KHÔNG đổi tên riêng (nhân vật, địa danh, môn phái, pháp bảo...).
- KHÔNG đổi con số / số lượng / đơn vị.
- KHÔNG đổi tông giọng hay phong cách của tác giả.
- KHÔNG tóm tắt, không lược bỏ, không "cải biên".
- **KHÔNG "chuẩn hoá" tiếng lóng, từ mạng, từ mượn thành văn viết.** `combat`,
  `combat mõm`, `skill`, `check`, `cớm`, `toang`, `phake`, `auth`, `plot`,
  `idol`, `oánh`, `tẩn`, `phốt`, `hóng`, `bá đạo hạt gạo`, `cmnr`, `xịn sò`,
  `cùi bắp`, `quay xe`, `vãi`... — đây KHÔNG phải lỗi dịch máy, đây là giọng
  truyện. Truyện hài mà dịch bằng văn phong nghiêm túc là làm hỏng nội dung.
  Đổi `combat`→`chiến đấu`, `cớm`→`công an`, `toang`→`nguy hiểm` là bản dịch
  TỆ HƠN, không phải sạch hơn.
  Vẫn được viết lại thoải mái câu dịch máy lủng củng (mục 3) — chỉ là viết lại
  cho mượt bằng CHÍNH giọng đó, đừng kéo nó về văn viết trung tính.
- **KHÔNG tự ý làm nhẹ nội dung nhạy cảm** (chửi thề, bạo lực, tình dục giữa
  người lớn) ngoài đúng một trường hợp CSAE ở mục 5. `assemble_qa.py` so bản QA
  với bản gốc và báo mọi từ nhạy cảm biến mất, nên việc âm thầm làm mờ sẽ lộ ra.
- KHÔNG thêm chủ thể, động cơ, cảm xúc, nguyên nhân, kết quả, hoặc quan hệ vốn chỉ
  là suy đoán từ ngữ cảnh.

## CHƯƠNG QUÁ DÀI (không có mốc `Chương` → 1 chương khổng lồ)
Nếu `text` rất dài, xử lý tuần tự theo từng đoạn văn xuôi (~3000 từ / đoạn),
sửa từng đoạn rồi nối lại ĐÚNG THỨ TỰ. Không đảo đoạn, không bỏ đoạn.

## VÍ DỤ (before → after)

1. **Ký tự Trung sót lại**
   - Trước: `Hắn vận 灵气 vào đan điền, cảm thấy 经脉 ấm dần.`
   - Sau:   `Hắn vận linh khí vào đan điền, cảm thấy kinh mạch ấm dần.`

2. **Pinyin lẫn trong câu**
   - Trước: `Sư phụ gọi hắn là xiao zi, giọng đầy trìu mến.`
   - Sau:   `Sư phụ gọi hắn là tiểu tử, giọng đầy trìu mến.`

3. **Câu dịch máy lủng củng**
   - Trước: `Đối với việc này của hắn mà nói thì là một loại không thể nào mà
     tiếp nhận được của sự thật.`
   - Sau:   `Với hắn, đây là một sự thật không thể chấp nhận.`

4. **Câu quá dài → tách**
   - Trước: `Hắn bước ra khỏi động phủ, nhìn bầu trời đầy sao đang xoay chuyển
     theo một quy luật cổ xưa mà hắn chưa từng hiểu rõ, trong lòng dâng lên một
     cảm giác vừa kính sợ vừa khao khát muốn vươn tới đỉnh cao của đại đạo mà bao
     đời tiền nhân đã ngã xuống.`
   - Sau:   `Hắn bước ra khỏi động phủ, nhìn bầu trời đầy sao xoay chuyển theo
     một quy luật cổ xưa hắn chưa từng hiểu rõ. Trong lòng dâng lên cảm giác vừa
     kính sợ vừa khao khát. Hắn muốn vươn tới đỉnh cao đại đạo — nơi bao đời
     tiền nhân đã ngã xuống.`

## OUTPUT CONTRACT
Ghi file `.work/qa-chapter-<NNN>.md` (NNN = chapter_id zero-padded 3 chữ số),
dùng `cache_key = sha1(input_hash + serialize(chapter_row))[:16]`:

```markdown
---
chapter_id: <id>
title: <title nguyên văn từ chapter_row, KHÔNG đổi>
cache_key: <16 hex>
---
<toàn bộ text chương đã hiệu đính, giữ phân đoạn paragraph>
```

Body = chỉ phần văn xuôi đã sửa. KHÔNG lặp lại title trong body (assemble_qa.py
sẽ tự render heading). Giữ các dòng trống giữa các paragraph.

## SELF-CHECK TRƯỚC KHI GHI
1. Quét lại body: còn ký tự CJK (U+4E00–U+9FFF) hay pinyin lạc lõng không? Nếu
   còn → dịch nốt.
2. Tên riêng / con số có khớp bản gốc không? Nếu lệch → khôi phục.
3. Còn câu nào > ~200 ký tự không? Nếu còn → tách.
4. Độ dài body có gần tương đương bản gốc không (không bị cắt mất đoạn)?
5. Nếu đây là chương đầu file, body vẫn giữ nguyên điểm bắt đầu truyện; không thêm
   câu nối tự chế để làm nó có vẻ liền mạch với file trước.
6. Đối chiếu từng đoạn với source: mọi tên, chủ thể, hành động, quan hệ nhân quả,
   cảm xúc và kết quả trong bản QA đều phải tồn tại trong đoạn gốc. Nếu không chỉ
   ra được câu nguồn, khôi phục cách diễn đạt sát chữ thay vì suy diễn.
7. **CSAE (mục 5):** quét từng câu — có câu nào vừa nhắc trẻ vị thành niên vừa có
   từ chỉ hành vi tình dục không? Còn một câu là kênh bị xoá. Sửa hết.
8. **Giọng truyện:** so bản QA với source — có từ lóng/từ mạng/từ mượn nào bị
   đổi thành văn viết không (`combat`, `cớm`, `toang`, `phake`, `skill`...)?
   Nếu có mà không phải do viết lại cả câu cho mượt → khôi phục nguyên trạng.

## STDOUT SUMMARY
```
QA chương <NNN>: <số sửa CJK> CJK, <số câu tách> câu dài tách, <wc> từ
```
