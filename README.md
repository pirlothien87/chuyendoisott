# Website quản lý tiến độ khảo nghiệm (MVP)

Bản này đã cập nhật theo BA spec trọng tâm:
- Đăng nhập email/password.
- Vai trò `admin/accountant/am/ctv/viewer`.
- Dùng **MySQL** thay cho SQLite.
- Rule hiển thị task theo RBAC:
  - Admin: thấy toàn bộ task.
  - AM: chỉ thấy task thuộc tỉnh được phân công.
  - CTV: chỉ thấy task được assign trực tiếp.
- Admin có màn hình tạo user cơ bản.

## Chạy nhanh bằng Docker Compose

1. Tạo file env:
```bash
cp .env.example .env.production
```
2. Chạy:
```bash
docker compose --env-file .env.production up -d --build
```
3. Mở web: `http://localhost:8000`

## Tài khoản mặc định

- Super admin: `superadmin@example.com / SuperAdmin@123`
- Accountant: `accountant@example.com / Accountant@123`
- AM: `am@example.com / Am@123456`
- CTV: `ctv@example.com / Ctv@123456`

## Lưu ý phạm vi hiện tại

Đây là MVP backend/server-rendered để chốt logic nghiệp vụ chính và môi trường chạy.
Các module lớn trong BA spec (contracts, import/export Excel, email gateway UI, logs, upload ảnh thực tế...) sẽ triển khai tiếp theo từng sprint.
