# User guide

## Đăng nhập
- Truy cập `/login` và đăng nhập bằng email/password.

## Quyền theo vai trò
- **Admin**: vào `/admin/users` để tạo user; xem toàn bộ task.
- **AM**: xem task trong tỉnh được gán.
- **CTV**: chỉ xem task được assign trực tiếp.
- **Accountant**: hiện tại có quyền đăng nhập, phần hợp đồng sẽ bổ sung theo sprint kế tiếp.

## Luồng tối thiểu hiện tại
1. Admin đăng nhập.
2. Admin tạo user.
3. Người dùng đăng nhập và kiểm tra task visibility tại `/tasks`.

## Tài khoản mặc định
- superadmin@example.com / SuperAdmin@123
- accountant@example.com / Accountant@123
- am@example.com / Am@123456
- ctv@example.com / Ctv@123456
