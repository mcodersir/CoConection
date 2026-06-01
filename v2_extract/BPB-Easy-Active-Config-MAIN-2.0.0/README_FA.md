# BPB/Nova Easy Active Config v2

ساخته شده توسط **mcoders** — https://github.com/mcodersir

این نسخه، BPB Easy را با یک لایه **Nova Easy Mode** ترکیب می‌کند تا کاربر تازه‌کار با چند کلیک به کانفیگ تست‌شده برسد.

## اجرای سریع

- ویندوز: `run_windows.bat`
- مک/لینوکس: `run_mac_linux.sh`

## مسیر ساده برای کاربر

۱. Atomic Mail یا ایمیل پروژه را آماده کن.
۲. Cloudflare را باز کن و حساب بساز/وارد شو.
۳. در نرم‌افزار API Token و Account ID را وارد کن.
۴. Deploy Worker را بزن.
۵. لینک Subscription را بگذار.
۶. روی **Start — خروجی کانفیگ سالم** بزن.
۷. فایل زیر را import کن:

```text
output/nova_best_config_only.txt
```

## خروجی‌های مهم

- `output/nova_best_config_only.txt` — بهترین کانفیگ فقط برای کپی/import
- `output/nova_working_configs.txt` — کانفیگ‌های سالم پشتیبان
- `output/nova_quick_import.txt` — بهترین + بکاپ‌ها
- `output/nova_clash_meta.yaml` — خروجی Clash/Mihomo
- `output/nova_report_FA.md` — گزارش فارسی
- `output/best_active_config.txt` — خروجی کلاسیک ابزار

## ادغام Nova-Proxy

Nova-Proxy قابلیت‌هایی مثل Simple Mode، Health Check، Best Config، QR، خروجی‌های کلاینت و روتینگ پیشرفته را مطرح می‌کند. در این نسخه، بخش‌های مناسب برای هدف ما به‌صورت شفاف در `src/nova_core.py` و `integrated_sources/Nova_Proxy_Core/` پیاده‌سازی شده‌اند.

> کد obfuscated وارد مسیر اجرایی نشده؛ این نسخه خوانا و قابل بررسی است.

## مستندات

- `docs/QUICK_START_FA.md`
- `docs/NOVA_INTEGRATION_FA.md`
- `docs/DEPLOY_ASSISTANT_FA.md`
- `docs/TROUBLESHOOTING_FA.md`
- `docs/SOURCES_FA.md`

## نکته

این ابزار تست سبک و عملی انجام می‌دهد و خروجی را بر اساس TCP/TLS/WebSocket/VLESS probe رتبه‌بندی می‌کند. تست نهایی همیشه داخل کلاینتی مثل Hiddify، NekoBox، v2rayN، Sing-box یا Clash/Mihomo انجام می‌شود.
