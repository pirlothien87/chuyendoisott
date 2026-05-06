# Thiết kế nghiệp vụ đầy đủ - Website quản lý tiến độ khảo nghiệm

## 1) Phạm vi bản thiết kế
Tài liệu này chốt **thiết kế nghiệp vụ full** theo BA spec cho các vai trò Admin, Kế toán, AM, CTV; bao gồm luồng nghiệp vụ, phân quyền, trạng thái, dữ liệu, API, notification/email và báo cáo.

---

## 2) Vai trò và phân quyền

### 2.1 Admin
- Quản trị toàn bộ: users, provinces, companies, contracts, tasks.
- Cấu hình Email Gateway/SMTP.
- Xem email logs, notification logs.
- Dashboard tổng hợp và export báo cáo.

### 2.2 Kế toán
- Tạo/sửa hợp đồng, quản lý công ty.
- Xem tiến độ hợp đồng.
- Import dữ liệu Excel cũ.
- Không có quyền assign/review task thực địa.

### 2.3 AM
- Chỉ quản lý task thuộc tỉnh được phân công.
- Tạo task từ hợp đồng.
- Assign/reassign CTV.
- Review task: approve / need_update / cancel.

### 2.4 CTV
- Chỉ thấy task được assign trực tiếp.
- Cập nhật trạng thái, comment, upload ảnh.
- Gửi task chờ duyệt cho AM.

---

## 3) Quy tắc visibility bắt buộc
- Admin: thấy toàn bộ task.
- Kế toán: không quản lý task thực địa.
- AM: thấy task khi `task.province_id` thuộc danh sách `user_provinces` của AM.
- CTV: thấy task khi `task.assigned_to_user_id = current_user.id`.

---

## 4) Luồng nghiệp vụ chuẩn
1. Kế toán tạo hợp đồng.
2. AM tạo task thủ công từ hợp đồng.
3. AM assign CTV -> task `draft -> assigned`.
4. CTV thực hiện -> `in_progress`, thêm comment/ảnh.
5. CTV submit review -> `waiting_review`.
6. AM review:
   - đạt -> `completed`
   - chưa đạt -> `need_update` (+ review_note)
7. Admin theo dõi dashboard/report/logs.

---

## 5) Trạng thái

### Contract status
- `draft`, `active`, `in_progress`, `completed`, `cancelled`

### Task status
- `draft`, `assigned`, `in_progress`, `waiting_review`, `need_update`, `completed`, `cancelled`

---

## 6) Thiết kế dữ liệu (chuẩn hóa)
Các bảng tối thiểu cần có:
- `users`
- `provinces`
- `user_provinces`
- `companies`
- `contracts`
- `tasks`
- `task_comments`
- `task_photos`
- `task_status_logs`
- `system_settings`
- `notifications`
- `email_logs`

Ghi chú:
- SMTP credentials không hard-code, lưu env hoặc `system_settings` mã hóa.
- Tránh typo key: dùng `email.smtp_secure` (không dùng `enail.smtp_secure`).

---

## 7) API nghiệp vụ (chuẩn REST)

### Auth
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

### Users / Provinces
- `GET/POST/PUT/DELETE /api/users`
- `POST /api/users/:id/provinces`
- `GET/POST/PUT/DELETE /api/provinces`

### Companies / Contracts
- `GET/POST/PUT/DELETE /api/companies`
- `GET/POST/PUT/DELETE /api/contracts`
- `GET /api/contracts/:id/tasks`

### Tasks
- `GET/POST/PUT/DELETE /api/tasks`
- `POST /api/tasks/:id/assign`
- `POST /api/tasks/:id/status`
- `POST /api/tasks/:id/comments`
- `POST /api/tasks/:id/photos`
- `POST /api/tasks/:id/submit-review`
- `POST /api/tasks/:id/approve`
- `POST /api/tasks/:id/request-update`
- `POST /api/tasks/:id/cancel`

### Dashboard/Reports
- `GET /api/dashboard/summary`
- `GET /api/dashboard/tasks-by-status`
- `GET /api/dashboard/tasks-by-province`
- `GET /api/dashboard/tasks-by-am`
- `GET /api/dashboard/tasks-overdue`
- `GET /api/export/contracts`
- `GET /api/export/tasks`
- `GET /api/export/progress-report`

### Notification / Email
- `GET/PUT /api/settings/email`
- `POST /api/settings/email/test`
- `GET /api/notifications`
- `POST /api/notifications/:id/read`
- `POST /api/notifications/read-all`
- `GET /api/email-logs`
- `GET /api/email-logs/:id`
- `POST /api/email-logs/:id/resend`

---

## 8) Ma trận quyền chức năng
| Chức năng | Admin | Kế toán | AM | CTV |
|---|---:|---:|---:|---:|
| Tạo hợp đồng | Có | Có | Không | Không |
| Tạo/assign task | Có | Không | Có (theo tỉnh) | Không |
| Reassign task | Có | Không | Có (theo tỉnh) | Không |
| Cập nhật task | Có | Không | Có | Có (task assigned) |
| Duyệt hoàn thành | Có | Không | Có | Không |
| Quản lý user/province | Có | Không | Không | Không |
| Cấu hình email gateway | Có | Không | Không | Không |

---

## 9) Email events bắt buộc
- `task_assigned`
- `task_reassigned`
- `task_in_progress`
- `task_comment_added`
- `task_photo_uploaded`
- `task_waiting_review`
- `task_need_update`
- `task_completed`
- `task_cancelled`
- `task_due_soon`
- `task_overdue`

Mọi lần gửi email cần log vào `email_logs` (`sent/failed`, `error_message`).

---

## 10) Giao diện bắt buộc
- Login page.
- Admin dashboard.
- Contract list/detail/create/edit.
- Task list/detail/create/edit.
- My Tasks (CTV, mobile-first card layout).
- User management.
- Province management.
- Company management.
- Import Excel.
- Export report.
- Email gateway settings.
- Notification center.
- Email logs.

---

## 11) Kế hoạch triển khai theo phase

### Phase 1 (đã có một phần)
- Auth + RBAC + MySQL + user/province/task visibility.

### Phase 2
- Companies + Contracts CRUD + filters + progress.
- Task workflow đầy đủ (assign/reassign/review logs).

### Phase 3
- Upload ảnh, comment timeline, in-app notification center.
- Email gateway + email logs + resend failed.

### Phase 4
- Dashboard nâng cao + export/import Excel.
- Cron due soon/overdue + anti-spam rules.

---

## 12) Tiêu chí nghiệm thu
1. CTV không thể thấy task không được assign.
2. AM không thể tạo/assign task ngoài tỉnh phụ trách.
3. Kế toán không thể duyệt task.
4. Task status transitions đúng workflow.
5. Email logs có bản ghi thành công/thất bại cho event quan trọng.
6. Dashboard hiển thị số liệu tổng hợp đúng filter.
