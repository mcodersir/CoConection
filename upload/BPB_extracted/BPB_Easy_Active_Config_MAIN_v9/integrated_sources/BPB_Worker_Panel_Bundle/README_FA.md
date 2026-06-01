# BPB Worker Panel Bundle

فایل `worker.js` داخل همین پوشه قرار دارد و برای Deploy از داخل نرم‌افزار استفاده می‌شود. این Worker یک Subscription ساده VLESS over WebSocket تولید می‌کند و برای استفاده روی اکانت Cloudflare خود کاربر/تیم است.

متغیرهای قابل تنظیم داخل نرم‌افزار:

- UUID
- SUB_PATH
- PROXY_IP اختیاری

بعد از Deploy، مسیر Subscription پیش‌فرض `/sub` است.
