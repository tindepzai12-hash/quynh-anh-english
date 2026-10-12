# VIL English — tài liệu và luồng luyện tập

## Phạm vi quan sát

Đã mở tài khoản Premium người dùng cung cấp, các mục Tải tài liệu, Cambridge IELTS, IELTS VOL Recent Actual Test, Writing, Dictation, Destination và Speaking. Đây là quan sát giao diện, không truy cập mã nguồn hoặc prompt nội bộ của VIL.

- `/download-material`: 3 liên kết PDF Destination.
- `/destinations`: hộp thoại tải có thêm PDF 1400 thành ngữ/cụm từ và thư mục Drive dự phòng gồm 3 PDF khác. Đã tải cả 7 tệp, xác thực header PDF, đọc cấu trúc bằng pypdf, ghi SHA256/dung lượng/số trang ở `imports/vil-english/manifest.json`. Tổng 554.648.313 byte, 4.475 trang. B2 chính và dự phòng là hai phiên bản khác nhau; không gộp nhầm.
- Cambridge: giao diện 15 tập × 4 đề, Listening 40 câu/32 phút và Reading 40 câu/60 phút; điều hướng section, cờ đánh dấu, ghi chú, tạm dừng.
- VOL: 10 tập, số đề khác nhau; lọc theo dạng Reading/Listening.
- Dictation: ngẫu nhiên, điền chỗ trống, Cambridge, VOL, YouTube; bài theo section, đếm câu, chế độ gõ toàn câu/điền từ, nghe lại và kiểm tra.
- Writing: đã lưu danh mục nhìn thấy Task 1/2 trong thư mục research local. Trình viết có giới hạn 900 từ, hướng dẫn thời gian/độ dài và lựa chọn giám khảo Gemini/Tony/Simon. Chưa nộp bài thử nên chưa xác minh đầu ra AI hay thuật toán chấm phía VIL. Không khẳng định Listening của VIL dùng Gemini.
- Destination: thẻ có IPA, từ loại, nghĩa/định nghĩa, ví dụ song ngữ, phát âm, yêu thích và phân trang.

**7 PDF là các tệp tải được đã tìm thấy trong hai mục tải và Drive dự phòng. Chưa xuất toàn bộ bài tương tác Cambridge/VOL, audio đề, video YouTube hoặc mọi trang nội dung của VIL thành học liệu offline.** Danh mục đề không tương đương tải nội dung đầy đủ từng đề. Không gọi bộ tải này là toàn bộ website.

## Đã triển khai trong app Quỳnh Anh

- Mục `#listening`: mở audio tại thiết bị, transcript chuẩn do người học cung cấp, nghe lại/tốc độ/lặp audio, gõ câu, Ctrl+Enter, đối chiếu từ đúng/sai/thiếu/thừa, luyện lại. Có 3 câu mẫu tự viết bằng TTS trình duyệt, được ghi rõ không phải audio IELTS. Audio không upload lên máy chủ.
- Điểm khớp transcript dùng Levenshtein, bỏ qua hoa/thường và dấu câu, giữ sự khác biệt giữa từ và dạng rút gọn. Mỗi đoạn tối đa 350 từ; không quy đổi sang band Listening, không cấp xu từ điểm tự nhập transcript.
- Gemini chỉ nhận văn bản transcript/câu gõ/kết quả đối chiếu để giải thích lỗi; không tự nhận đã nghe audio. Điểm deterministic không bị LLM thay đổi.
- Writing dùng cùng adapter, nhận xét 4 tiêu chí và 3 ưu tiên sửa, trích câu thật trong bài. Không tạo điểm IELTS chính thức hoặc giả vờ có band khi chưa đánh giá thật.
- Adapter Gemini REST và OpenAI cũ nằm phía máy chủ. API key không nằm trong URL, frontend hoặc GitHub. Giới hạn yêu cầu AI 20/15 phút/IP; giữ chặn hỗ trợ AI khi thi, đăng nhập trên cloud và kiểm tra Origin hiện có.
- Giao diện thông báo đúng nhà cung cấp đã cấu hình, nói rõ dữ liệu được gửi khi bấm yêu cầu AI. Có trạng thái chưa kết nối khi thiếu key/model. Không dùng giả phản hồi AI trong sản phẩm.

PDF tải nằm tại `imports/vil-english/materials`, không chép vào public/GitHub hoặc Render. Quyền tải tài liệu không được diễn giải thành yêu cầu đăng lại bộ PDF lên một website công khai.

## Kiểm thử

10 unit test Python: alignment, thiếu/thừa/rút gọn/dấu câu, giới hạn đầu vào, chưa có cấu hình, request Gemini và role mapping (mock), loại thought, chặn output bị cắt, model URL, consent, Writing 4 tiêu chí. Mock không xác minh kết nối API thật.

UI local đã đối chiếu câu sai 71% và câu đúng 100%, Ctrl+Enter, AI bị tắt khi chưa cấu hình. Đã mở fixture WAV tổng hợp 1 giây qua file chooser, xác nhận playbackRate=0.75, loop=true và nguồn blob tại thiết bị; trở về câu mẫu giải phóng nguồn. Mobile 390×844 không tràn ngang, console không warning/error; Writing khi thiếu key thông báo chưa gửi bài và nút AI bị tắt. Thêm 5 HTTP check local thành công: status, điểm, validation, Origin và AI chưa cấu hình. Không dùng bài riêng tư hoặc microphone trong QA. Tài khoản VIL không được nộp bài, viết bình luận hoặc đổi cài đặt.

## Cấu hình Gemini sau này

Trong Environment riêng của Render:

```
AI_PROVIDER=gemini
GEMINI_API_KEY=<key riêng, không đưa vào chat/git>
GEMINI_MODEL=<model hiện có trong Google AI Studio>
```

Khởi động lại/redeploy rồi kiểm tra `/api/ai-status`. `configured=true` chỉ nghĩa là đủ cấu hình hợp lệ, chưa chứng minh key hoạt động; cần một lượt gọi thật với bài thử không chứa dữ liệu riêng tư. Hiện chưa có key, chưa gọi Gemini thật, chưa xác minh hạn mức/model trong tài khoản. Theo lựa chọn người dùng, mới chuẩn bị tích hợp.

Tài liệu API chính thức đã kiểm tra: https://ai.google.dev/api/generate-content và https://ai.google.dev/gemini-api/docs/api-key . Model được chọn qua cấu hình thay vì đóng cứng một tên có thể hết hiệu lực.
