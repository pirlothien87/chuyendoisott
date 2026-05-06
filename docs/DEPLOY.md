# Deploy production (Docker Compose + MySQL)

## 1) Chuẩn bị server
- Cài Docker + Docker Compose plugin.
- Mở port `8000` (app) và `3306` nếu cần truy cập DB ngoài.

## 2) Cấu hình biến môi trường
```bash
cp .env.example .env.production
```
Cập nhật bắt buộc:
- `SECRET_KEY`
- `DB_PASSWORD`
- `MYSQL_ROOT_PASSWORD`
- `DEFAULT_ADMIN_PASSWORD`

## 3) Build + run
```bash
docker compose --env-file .env.production up -d --build
```

## 4) Kiểm tra
```bash
docker compose ps
docker compose logs -f app
```

## 5) Nâng cấp bản mới
```bash
git pull
docker compose --env-file .env.production up -d --build
```
