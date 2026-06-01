# ادغام Nova-Proxy در نسخه ۲

هدف این ادغام این است که قابلیت‌های سخت Nova برای کاربر معمولی به چند کلیک تبدیل شود.

## چه چیزهایی از Nova وارد شده؟

- Simple Mode / Easy Mode: کاربر فقط Start را می‌زند.
- Health Check: قبل از خروجی گرفتن، کانفیگ‌ها تست می‌شوند.
- Best Config: بهترین کانفیگ بر اساس score، latency و سیگنال‌های واقعی مثل VLESS/WebSocket انتخاب می‌شود.
- Local Sub Generation: خروجی‌ها داخل سیستم تولید می‌شوند و API خارجی برای تبدیل کانفیگ لازم نیست.
- Clash/Mihomo Export: فایل `nova_clash_meta.yaml` ساخته می‌شود.
- Copy/Import آماده: فایل `nova_best_config_only.txt` فقط خود کانفیگ را دارد.

## چرا سورس obfuscated وارد نشد؟

چون کاربر قبلاً درست گفت اجرای کد مبهم روی سیستم قابل اعتماد نیست. بنابراین منطق Nova به شکل شفاف و قابل بررسی در `src/nova_core.py` پیاده‌سازی شده است.

## خروجی‌ها

- `output/nova_best_config_only.txt` — اولین فایل برای import
- `output/nova_working_configs.txt` — همه کانفیگ‌های سالم
- `output/nova_quick_import.txt` — بهترین + بکاپ‌ها
- `output/nova_clash_meta.yaml` — خروجی Clash/Mihomo
- `output/nova_bundle.json` — گزارش ماشینی
- `output/nova_report_FA.md` — گزارش فارسی
