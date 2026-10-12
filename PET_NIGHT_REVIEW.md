# Justin Mini — kết quả kiểm tra đêm 2026-10-12

Kế hoạch trước chỉnh sửa: `PET_NIGHT_PLAN.md`. Hình trước/sau: `artifacts/pet-night/`.

## Các lỗi đã phát hiện và sửa

| Lỗi quan sát | Cách sửa và bằng chứng |
|---|---|
| Bụng xuyên áo | Che mesh bụng dưới áo kín; nới độ sâu áo; render và GLB test với cả 4 bộ |
| Tóc xuyên mũ | Thu tóc trong mũ khi đội, khôi phục khi tháo; thử cùng mọi bộ đồ |
| Mắt ngủ nổi thành khối cầu | Dùng nét cong đặt trên bề mặt đầu; ẩn cover hình cầu |
| Ngủ nằm lơ lửng | Loại tư thế nằm ngang thiếu giường; thay bằng ngủ gật nghiêng đầu, chân đặt xuống |
| Thử mũ làm mất áo đang thử | Preview giữ nhiều nhóm đồ; hủy phối thử trở về đồ đã lưu |
| Nhiều bộ đồ cùng icon | Thumbnail render từ chính model; lọc theo nhóm |
| Nhãn trang trí “Đang mặc” | Đổi thành Đang dùng/Dùng ngay; đồ ăn vẫn Cho ăn |
| Nền sấm trỏ sai tên ảnh | Map storm tới asset thunder; browser xác nhận không còn ảnh hỏng |
| Đèn không ảnh hưởng căn phòng | Đổi màu key light của model và tông sáng phòng; đồ trang trí có bóng sàn |

## Tham khảo phim

Đã mở trailer chính thức [How to Train Your Dragon: The Hidden World](https://www.dreamworks.com/movies/how-to-train-your-dragon-the-hidden-world) và tài liệu [quy trình Raya](https://disneyanimation.com/process-raya/). Quan sát một phần trailer, không xem trọn phim. Bài học diễn xuất áp dụng là hướng mắt/chú ý, nghiêng đầu nhỏ, đuôi theo sau, chân được hỗ trợ. Tạo hình vẫn theo ảnh gốc của người dùng.

## Test thực tế

- Ma trận render: 6 loại phụ kiện × Idle/Wave/Sleep/Play + 6 góc nhìn = 30 ảnh mỗi vòng. Sau các sửa hình/mí/cổ áo/ngủ đều render lại. Bản cuối ở `after/matrix.jpg`; đối chiếu 2D ở `after/reference-and-angles.jpg`.
- Node: 9 kiểm thử tài khoản/HTTP/state/PKCE và 5 kiểm thử animation/GLB/shop qua. Lần chạy đầu thiếu QA_URL và thư mục TEMP khả dụng; chạy lại đúng máy chủ QA riêng đã qua.
- Test GLB thật: 5 kiểu outfit kết hợp mũ + lagoon, khôi phục đồ gốc; không NaN; chân Idle không dịch vị trí; mắt ngủ không hiện cover cầu; đủ 4 file nền.
- Python: nền miễn phí cấp một lần, đặt/tháo, mua từng nền trả xu đúng và request trùng không mua hai lần.
- Browser: đã thử toàn bộ 13 món không phải thức ăn; phối nhiều nhóm, hủy, lọc 4 khung cảnh, bắt đủ 5 bóng, mặc đồ ngủ + đặt nền rồi reload vẫn giữ trong QA DB. Không đụng DB học thật.
- Desktop 1280: Home/Path/Library/Writing/Speaking/Tests/Account không tràn ngang, không ảnh hỏng trong quan sát. Mobile **390×844**: Pet/Home/Path/Library/Writing/Account không tràn ngang. File `night-phone-checks.json` là kích thước được xác nhận; ảnh `night-mobile-*` ban đầu vẫn 1280 nên không dùng làm chứng cứ mobile.
- Console QA cuối lượt không warning/error. Detector tìm animation width ở thanh tiến trình; bỏ transition gây layout. Không phải chứng nhận WCAG hay test đầy đủ mọi nghiệp vụ học.

## Đánh giá UX và tạo hình

Luồng pet hiện rõ hơn: chơi/ngủ/chạm ở một hàng, nói riêng bên cạnh, shop có nhóm, preview báo chưa lưu. Home có nút học tiếp và Library có hình, lật thẻ, mức nhớ. Trên điện thoại shop vẫn dài khi chọn Tất cả; bộ lọc giải quyết tìm đồ nhưng chưa có thử nghiệm người dùng đo thời gian thao tác. Không xóa chức năng học hiện có.

Tạo hình dễ đọc và biểu cảm ngủ mềm hơn bản trước theo đánh giá thiết kế của tác giả. Chưa có chứng cứ rằng mọi người dùng thấy đủ dễ thương. Đầu vẫn tròn hơn mẫu 2D, mắt còn nổi khi nhìn ngang; cổ áo và tay chưa phải phục trang phim. Không có mô phỏng vải, IK chân hay vật lý va chạm tự động. Khung cảnh/cây/đèn là lớp 2D quanh model 3D, được ghi rõ ngay ở shop.

## Google ngày mai

`node/google-setup.json`, `node/check-google-setup.mjs`, `GOOGLE_READY_FOR_TOMORROW.md` đã chuẩn bị. Google/Facebook vẫn tắt; Google Cloud cần người dùng hoàn tất 2SV và cấp OAuth thật. Không tự tạo quyền hoặc đổi bảo mật khi người dùng đang ngủ.

## Đề xuất còn lại

Lần sửa tạo hình tiếp theo nên ưu tiên đầu quả lê/mắt ôm mặt, rồi tay ôm bụng. Tránh thêm nhiều đồ mới trước khi duyệt phong cách. Các điểm này chưa được gọi là hoàn thành.

## Bổ sung giường theo yêu cầu mới

Đã thêm giường 3D miễn phí với khung xanh dịu, nệm kem, gối và đầu giường. Khi chọn Ngủ một chút, Justin nằm nghiêng; thân được đặt theo bounding box biến dạng trên mặt nệm, gối đặt dưới đầu. Khi thức dậy, giường ẩn và scale/vị trí nhân vật được phục hồi. Không thêm món phải mua hoặc trừ xu.

Kiểm tra 6 test Node thành công, gồm GLB thật với 5 bộ đồ + mũ, điểm tiếp xúc nệm và tính ổn định khi căn vị trí lặp lại. UI local xác nhận ngủ → thức → ngủ, phối school + cap lúc ngủ vẫn giữ trạng thái ngủ. Ảnh desktop và điện thoại 390×844 ở `artifacts/pet-night/after/justin-bed*.png`; điện thoại không tràn ngang, console không warning/error. Giường và nhân vật hiển thị đủ trong khung. Đây là tư thế dựng sẵn và căn điểm tựa, chưa phải mô phỏng vật lý/va chạm vải.
