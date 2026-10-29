"""Official web upload destinations; deliberately distinct from an OAuth connection."""

DESTINATIONS = {
    "youtube": {
        "label": "YouTube Studio",
        "upload_url": "https://studio.youtube.com/",
        "account_note": "Tự chọn audience/made-for-kids; Kids không có cổng upload riêng.",
    },
    "tiktok": {
        "label": "TikTok Studio",
        "upload_url": "https://www.tiktok.com/tiktokstudio/upload",
        "account_note": "Cần tài khoản đủ điều kiện; hoàn tất đăng trong TikTok Studio.",
    },
    "facebook": {
        "label": "Facebook Reels",
        "upload_url": "https://www.facebook.com/reels/create/",
        "account_note": "Trang đăng thực tế có thể khác theo tài khoản/Page và khu vực.",
    },
}


def upload_hub() -> dict:
    return {
        "mode": "manual_web_upload",
        "direct_upload_implemented": False,
        "connected": False,
        "note": "Tải MP4 về rồi mở trang đăng. Mở link không kết nối OAuth và không tự gửi tệp.",
        "providers": DESTINATIONS,
        "oauth_requirements": {
            "youtube": "Google OAuth, youtube.upload scope, verification/audit theo dự án.",
            "tiktok": "Ứng dụng Content Posting API, video.upload và quyền được phê duyệt; inbox khác publish.",
            "facebook": "Meta app, Page phù hợp, Page access token và quyền/app review cần thiết.",
        },
    }
