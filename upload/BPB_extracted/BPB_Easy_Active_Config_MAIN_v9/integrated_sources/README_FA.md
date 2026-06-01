# سورس‌های ادغام‌شده داخل پروژه

این پوشه برای نسخه v7 ساخته شده تا کاربر به GitHub یا ابزارهای جداگانه نرود. منطق لازم از سه پروژه در هسته برنامه ادغام شده است:

- `BPB_Wizard_Internal`: جریان داخلی نصب/Deploy Assistant برای Cloudflare.
- `BPB_Worker_Panel_Bundle`: Worker داخلی سازگار با Subscription ساده VLESS over WebSocket.
- `SenPaiScanner_Core`: اسکنر داخلی IP/Port با تست HTTP/TLS و خروجی clean_ips.txt.
- `Rasoul_Config_Modifier`: تولید گروهی کانفیگ با جایگزینی Endpoint/IP/Port.

نکته: این نسخه برای استفاده روی اکانت Cloudflare خود کاربر/تیم طراحی شده است.
