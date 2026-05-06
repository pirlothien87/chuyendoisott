# Hướng dẫn sử dụng web

## URL truy cập
- Local/dev: `http://localhost:8000`

## Đăng nhập mặc định (super admin)
- Username: `superadmin`
- Password: `SuperAdmin@123`

> Sau lần đăng nhập đầu tiên trên production, bắt buộc đổi mật khẩu mặc định.

## Luồng sử dụng cơ bản
1. Mở trang `/login`.
2. Nhập tài khoản super admin.
3. Sau khi đăng nhập thành công sẽ vào `/dashboard`.
4. Bấm `Logout` để thoát phiên.

## Lưu ý vận hành
- Nếu quên mật khẩu mặc định đã đổi: reset trực tiếp trong DB hoặc tạo script admin reset.
- Theo dõi log bằng `docker compose logs -f web`.
