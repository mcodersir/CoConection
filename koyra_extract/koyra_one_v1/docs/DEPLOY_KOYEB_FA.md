# نصب Koyra One روی Koyeb — مرحله‌ای

## ۱) آماده‌سازی فایل‌ها

این پروژه شامل این فایل‌هاست:

```text
server.js
package.json
.env.example
```

اگر می‌خواهی واقعاً فقط یک فایل داشته باشی، `server.js` کافی است؛ ولی برای Deploy راحت روی Koyeb بهتر است `package.json` هم کنار آن باشد.

## ۲) ساخت پروژه در GitHub

یک ریپو خصوصی یا عمومی بساز و این دو فایل را داخلش بگذار:

```text
server.js
package.json
```

## ۳) ساخت سرویس در Koyeb

1. وارد Koyeb شو.
2. روی **Create App** یا **Create Web Service** بزن.
3. Source را GitHub انتخاب کن.
4. ریپو را انتخاب کن.
5. Runtime باید Node.js تشخیص داده شود.
6. Start command اگر لازم شد:

```bash
npm start
```

Koyeb برای Web Services متغیر `PORT` را خودش تعریف می‌کند و برنامه هم از همان استفاده می‌کند.

## ۴) تنظیم Environment Variables

در مرحله Deploy یا بعداً از Settings این‌ها را اضافه کن:

```text
KOYRA_KEY=یک متن طولانی و خصوصی
KOYRA_PATH=/koyra
KOYRA_REMARK=Koyra-One
```

پیشنهادی برای خصوصی‌تر شدن Subscription:

```text
KOYRA_SUB_TOKEN=یک-توکن-خصوصی-بلند
```

## ۵) بعد از Deploy

دامنه سرویس را باز کن:

```text
https://YOUR-SERVICE.koyeb.app/
```

حالا روی دکمه Subscription بزن یا این لینک را در کلاینت وارد کن:

```text
https://YOUR-SERVICE.koyeb.app/sub
```

اگر token گذاشتی:

```text
https://YOUR-SERVICE.koyeb.app/sub/TOKEN
```

## ۶) Import در کلاینت

در v2rayN، NekoBox، Hiddify یا Sing-box لینک Subscription را وارد کن.

اگر کانفیگ مستقیم خواستی:

```text
https://YOUR-SERVICE.koyeb.app/config
```

## نکته فنی

Koyeb از Node.js app و WebSocket app پشتیبانی می‌کند و برای سرویس‌های Web یک `PORT` تعریف می‌کند. پس برنامه فقط روی `process.env.PORT` گوش می‌دهد.
