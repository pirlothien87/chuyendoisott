# Hướng dẫn deploy production

## 1) Chuẩn bị server
- Có Docker + Docker Compose plugin.
- Mở port 80/443 (nếu dùng reverse proxy).

## 2) Pull code và cấu hình env
```bash
git clone <repo-url>
cd chuyendoisott
cp .env.example .env
```

Cập nhật `.env`:
- `SECRET_KEY`: giá trị mạnh và khó đoán.
- `DEFAULT_ADMIN_PASSWORD`: đổi ngay mật khẩu mặc định.

## 3) Build và chạy
```bash
docker compose up -d --build
docker compose ps
docker compose logs -f web
```

## 4) Cấu hình domain + SSL
Khuyến nghị đặt Nginx/Caddy phía trước container và terminate SSL.

## 5) Cập nhật phiên bản
```bash
git pull
docker compose up -d --build
```

## 6) Sao lưu dữ liệu
Dữ liệu SQLite nằm trong volume `app_data`. Cần backup định kỳ volume này.
