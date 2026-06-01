# Nova Proxy Core — ادغام داخلی

این پوشه بخش شفاف و قابل بررسی ادغام Nova-Proxy در پروژه mcoders است.

به‌جای وارد کردن فایل obfuscated، قابلیت‌های مستند Nova به شکل ماژول خوانا پیاده‌سازی شده‌اند:

- Nova Easy Mode برای کاربر عادی
- انتخاب خودکار بهترین کانفیگ بر اساس سلامت واقعی، WebSocket/VLESS probe، امتیاز و latency
- خروجی import سریع: `nova_best_config_only.txt`
- خروجی پشتیبان: `nova_working_configs.txt`
- خروجی Clash/Mihomo: `nova_clash_meta.yaml`
- گزارش فارسی: `nova_report_FA.md`

منبع الهام: https://github.com/IRNova/Nova-Proxy
