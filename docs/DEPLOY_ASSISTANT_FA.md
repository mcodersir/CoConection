# آموزش دقیق Deploy Assistant

این راهنما برای کسی است که هیچ چیزی از Cloudflare Workers و BPB نمی‌داند.

## ۱) آماده کردن ایمیل

- اگر تیم/پروژه برایت Atomic Mail داده، همان ایمیل را استفاده کن.
- اگر ایمیل نداری، داخل نرم‌افزار روی «باز کردن Atomic Mail» بزن و ایمیل قابل‌دسترسی بساز.
- این ایمیل را برای Cloudflare وارد کن.

## ۲) ساخت/ورود Cloudflare

داخل نرم‌افزار روی «باز کردن ثبت‌نام Cloudflare» بزن.

در صفحه Cloudflare:

1. Email را وارد کن.
2. Password را وارد کن.
3. وارد Dashboard شو.
4. اگر Cloudflare ازت Account Name خواست، یک نام ساده بزن، مثلاً `BPB Team`.
5. بعد داخل نرم‌افزار روی «باز کردن Workers & Pages» بزن.
6. صفحه Workers & Pages را یک بار باز کن تا workers.dev برای اکانت آماده شود.

## ۳) ساخت API Token

داخل نرم‌افزار در مرحله Deploy Assistant روی «باز کردن صفحه API Tokens» بزن.

در Cloudflare:

1. برو به `My Profile → API Tokens`.
2. روی `Create Token` بزن.
3. اگر قالب آماده برای Workers دیدی می‌توانی استفاده کنی؛ وگرنه `Create Custom Token` را بزن.
4. در Permissions این دسترسی را اضافه کن:
   - `Account → Workers Scripts → Edit`
5. در Account Resources همان Account خودت/تیمت را انتخاب کن.
6. روی `Continue to summary` بزن.
7. روی `Create Token` بزن.
8. توکن را کپی کن. این توکن فقط یک بار کامل نشان داده می‌شود.
9. برگرد به نرم‌افزار و توکن را در فیلد `Cloudflare API Token` Paste کن.

## ۴) پیدا کردن Account ID درست

بهترین روش داخل نرم‌افزار:

1. Token را Paste کن.
2. روی «تست Token و پیدا کردن Account ID» بزن.
3. اگر حساب پیدا شود، فیلد Account ID خودکار پر می‌شود.

روش دستی:

1. داخل Cloudflare برو به `Workers & Pages`.
2. در بخش `Account details` دنبال `Account ID` بگرد.
3. روی `Click to copy` بزن.
4. مقدار را در فیلد Account ID نرم‌افزار Paste کن.

## ۵) خطای cfat_ یعنی چه؟

اگر این خطا را دیدی:

```text
Could not route to /client/v4/accounts/cfat_.../workers/scripts/bpb-panel
```

اشتباه این است که API Token را داخل فیلد Account ID گذاشته‌ای.

- `cfat_...` یا `cfut_...` = Token
- Account ID = شناسه اکانت، معمولاً ۳۲ کاراکتری مثل عدد و حروف a-f

راه حل:

1. مقدار فیلد Account ID را پاک کن.
2. روی «تست Token و پیدا کردن Account ID» بزن.
3. اگر پیدا نشد، دستی از `Workers & Pages → Account details → Account ID` کپی کن.

## ۶) Deploy Worker داخلی

در نرم‌افزار:

1. Worker Name را همان `bpb-panel` بگذار.
2. روی «ساخت UUID امن» بزن.
3. Subscription Path را `sub` بگذار.
4. Proxy IP اختیاری است؛ برای شروع خالی بگذار.
5. روی «Deploy فایل BPB داخلی» بزن.

اگر موفق بود، نرم‌افزار لینک پیشنهادی Subscription را می‌دهد. اگر لینک نداد:

1. Cloudflare را باز کن.
2. برو `Workers & Pages`.
3. روی `bpb-panel` بزن.
4. روی `Visit` بزن.
5. آدرس را با `/sub` باز کن؛ مثل:

```text
https://bpb-panel.YOUR-SUBDOMAIN.workers.dev/sub
```

## ۷) گرفتن کانفیگ نهایی

1. لینک Subscription را در مرحله Subscription نرم‌افزار Paste کن.
2. روی «دریافت و بررسی لینک» بزن.
3. اول حالت «فقط تست کانفیگ‌های BPB» را بزن.
4. اگر نتیجه ضعیف بود، برگرد IP Scanner را اجرا کن.
5. سپس حالت «ترکیب BPB با Clean IP» را بزن.
6. خروجی نهایی در `output/best_active_config.txt` است.
