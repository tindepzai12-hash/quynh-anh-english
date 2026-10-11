# Google login: cấu hình đã chuẩn bị, chưa kích hoạt

App đã có OAuth PKCE, lưu verifier vào session phía server, callback và giao diện bật theo provider. Giữ `GOOGLE_OAUTH_ENABLED=false` và Facebook tắt cho tới khi có thông tin thật.

`node/google-setup.json` chứa cấu hình công khai. `node/check-google-setup.mjs` kiểm tra origin/cờ/có khóa backend, không in khóa bí mật. Chạy với biến môi trường thực tế của máy chủ; không gửi file `.env` lên GitHub.

## Ngày mai thực hiện

1. Chủ tài khoản bật 2-Step Verification theo yêu cầu Google Cloud. Không cần gửi OTP/mật khẩu vào chat.
2. Google Cloud: chọn/tạo project, Google Auth Platform > Branding/Audience/Data Access. Tên ứng dụng: học tiếng anh cùng bé iu QUỲNH ANH. Chỉ dùng email/profile/openid cho đăng nhập. Khi ở Testing, thêm tài khoản thử nghiệm.
3. Clients > Web application. Origin: `https://quynh-anh-english.onrender.com`. Redirect URI Google phải là callback của **Supabase**, lấy nguyên văn trong provider Google, dạng `https://<project-ref>.supabase.co/auth/v1/callback`.
4. Điền Client ID và Client Secret riêng vào provider Google của Supabase. Đây là tạo quyền truy cập lâu dài; cần xác nhận ngay trước thao tác qua UI. Không đưa secret vào frontend/Render/GitHub.
5. Supabase URL Configuration: Site URL `https://quynh-anh-english.onrender.com`; allow redirect tới `/auth/callback` của site và localhost. App hiện gắn `?state=...`; xác minh URL allowlist nhận query này trong flow thực tế. Chỉ dùng wildcard trên callback nếu thực sự cần, không mở mọi domain.
6. Sau khi provider cấu hình đúng, bật `GOOGLE_OAUTH_ENABLED=true` trên Render; Facebook vẫn false. Không thay SESSION_SECRET và không reset database.
7. Test tài khoản thật: lần đầu đăng nhập, logout/login lại, từ chối consent, callback hết hạn, lưu và tải tiến trình, kiểm tra điện thoại. Chưa qua các bước này thì không ghi “Google đã hoạt động”.

Nguồn đã đối chiếu ngày 2026-10-12: [Supabase Google](https://supabase.com/docs/guides/auth/social-login/auth-google), [redirect URLs](https://supabase.com/docs/guides/auth/redirect-urls).
