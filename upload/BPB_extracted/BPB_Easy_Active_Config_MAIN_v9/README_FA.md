# BPB Easy Active Config MAIN v9.0.0

ساخته شده توسط **mcoders**  
https://github.com/mcodersir

این نسخه برای کاربر غیرتخصصی طراحی شده: کاربر فقط از داخل Wizard جلو می‌رود و نهایتاً برای ایمیل پروژه/Atomic Mail و Cloudflare از برنامه خارج می‌شود.

## اجرای سریع

### ویندوز
روی فایل زیر دابل‌کلیک کن:

```bat
run_windows.bat
```

### مک / لینوکس

```bash
chmod +x run_mac_linux.sh
./run_mac_linux.sh
```

## مسیر ساده برای کاربر

1. برنامه را اجرا کن.
2. در مرحله ایمیل، اگر تیم Atomic Mail داده همان را استفاده کن.
3. وارد Cloudflare شو.
4. در مرحله Deploy، API Token را Paste کن.
5. روی «تست Token و پیدا کردن Account ID» بزن.
6. UUID بساز و «Deploy فایل داخلی» را بزن.
7. لینک Subscription را داخل مرحله Config Test بگذار.
8. حالت هوشمند را دست نزن و «شروع اجرا و ساخت خروجی قابل تست» را بزن.
9. خروجی نهایی را از مرحله آخر کپی کن.

## خروجی‌ها

- `output/best_active_config.txt` بهترین کانفیگ پیشنهادی
- `output/working_configs.txt` همه کانفیگ‌هایی که تست OK داده‌اند
- `output/top_active_configs.txt` ۵۰ خروجی برتر تست‌شده
- `output/scan_results.json` گزارش فنی تست کانفیگ‌ها
- `output/clean_ips.txt` خروجی اسکن کیفیت IP

## رابط کاربری

- کاملاً RTL و فارسی
- ریسپانسیو برای موبایل، تبلت و دسکتاپ
- بدون CDN خارجی برای CSS/JS/Icon
- آیکون‌ها و استایل‌ها داخل پروژه هستند

## درباره تست اتصال

نسخه v9 برای کانفیگ‌های VLESS over WebSocket فقط به TCP/TLS اکتفا نمی‌کند؛ تا حد امکان WebSocket Upgrade و یک Probe سبک VLESS را هم تست می‌کند. این باعث می‌شود خروجی نهایی نزدیک‌تر به کانفیگ واقعاً قابل استفاده باشد.

## منابع ادغام‌شده

- BPB Worker Panel برای ایده پنل و Subscription
- SenPaiScanner برای ایده اسکن endpointهای Cloudflare
- v2ray-config-modifier برای ایده تولید گروهی کانفیگ با Endpointهای مختلف

سورس‌های قابل استفاده داخل `integrated_sources/` قرار دارند و UI کاربر را به GitHub نفرستاده است.
