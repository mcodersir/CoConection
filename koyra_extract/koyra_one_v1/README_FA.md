# Koyra One v1 — کویرا وان

**Koyra One** اسم روش نسخه اول ماست: یک فایل ساده JS برای ساخت کانفیگ شخصی VLESS روی Koyeb.

این نسخه برای استفاده شخصی طراحی شده: یک نفر، یک سرویس، یک کانفیگ تمیز. کد شفاف است، obfuscation ندارد، dependency خارجی ندارد و با `node server.js` اجرا می‌شود.

## ایده روش

Koyra One روی Koyeb یک HTTP/WebSocket service اجرا می‌کند. کاربر وقتی دامنه سرویس را باز کند، خودش این‌ها را می‌گیرد:

- لینک Subscription
- کانفیگ خام `vless://...`
- خروجی JSON ساده برای Sing-box
- Health check

## فایل اصلی

```bash
server.js
```

همین فایل هسته کار است. `package.json` فقط برای این است که Koyeb راحت‌تر Node.js را تشخیص بدهد و دستور start داشته باشد.

## متغیرهای مهم Koyeb

داخل Koyeb در بخش Environment Variables این‌ها را بگذار:

```text
KOYRA_KEY=یک_متن_طولانی_خصوصی_و_تصادفی
KOYRA_PATH=/koyra
KOYRA_REMARK=Koyra-One
```

اگر می‌خواهی لینک Subscription عمومی نباشد:

```text
KOYRA_SUB_TOKEN=یک-توکن-خصوصی
```

بعد لینک subscription می‌شود:

```text
https://YOUR-SERVICE.koyeb.app/sub/یک-توکن-خصوصی
```

اگر `KOYRA_SUB_TOKEN` نگذاری، لینک ساده است:

```text
https://YOUR-SERVICE.koyeb.app/sub
```

## خروجی کانفیگ

بعد از Deploy، دامنه Koyeb را باز کن:

```text
https://YOUR-SERVICE.koyeb.app/
```

همان صفحه، کانفیگ را نشان می‌دهد.

## مسیرها

```text
/             پنل ساده فارسی
/health       وضعیت سرویس
/sub          Subscription base64
/config       کانفیگ خام vless://
/json         خروجی Sing-box JSON
```

اگر `KOYRA_SUB_TOKEN` تنظیم کرده باشی، مسیرها به این شکل می‌شوند:

```text
/sub/TOKEN
/config/TOKEN
/json/TOKEN
```

## محدودیت نسخه ۱

این نسخه عمداً ساده است:

- فقط VLESS over WebSocket را پیاده‌سازی می‌کند.
- UDP در نسخه ۱ پشتیبانی نمی‌شود.
- Reality/Trojan/VMess ندارد.
- برای استفاده شخصی سبک است، نه فروش یا تعداد کاربر زیاد.

## تست محلی

```bash
KOYRA_KEY=test-key node server.js
```

بعد باز کن:

```text
http://127.0.0.1:3000/
```

## امنیت

- `KOYRA_KEY` را حتماً عوض کن.
- فایل را obfuscate نکن؛ کاربر باید بتواند کد را بخواند.
- برای اشتراک‌گذاری، `KOYRA_SUB_TOKEN` بگذار.
- این ابزار را فقط برای مصرف شخصی و مجاز استفاده کن.

ساخته شده برای روش **Koyra One**.
