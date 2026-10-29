# Quy ước

## Đặt tên và cấu trúc

Python snake_case, TS camelCase, DTO API snake_case. Ruff format/check và Prettier cho frontend; không tắt assertion/rule để đạt pass. Dependency lockfile bắt buộc.

## Xử lý lỗi

DomainError code/message/status tại ranh giới API. Không log nội dung lời thoại/token/đường dẫn riêng. Worker lưu lỗi hữu hạn, không giả success. Model/mock phải ghi đúng trạng thái.

## Giao diện

Light kem#F7F5EE, cardtrắng, xanh#254D3D; contrast đã kiểm axe hai màn. Chữ phụ#526347. Control44px, focus3px, responsive390px. Hiển thị tiếng Việt; reduced motion. Renderer dùng font Noto đóng gói, không text trong ảnhAI.

## Commit

- Nền: github.
- [Type] - Description, theo spec; user cho phép commit/push nhánhfeat/short-video-studio, không force/main reset.
