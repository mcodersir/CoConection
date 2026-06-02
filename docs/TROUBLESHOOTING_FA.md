# خطایابی سریع

## خطای Content-Type هنگام Deploy
نسخه v9 همان فیکس v9 را نگه داشته است: Worker با `multipart/form-data` و metadata دارای `main_module: worker.js` ارسال می‌شود.

## خطای accounts/cfat_...
یعنی API Token را داخل Account ID گذاشته‌ای. راه درست:

1. API Token را در فیلد API Token بگذار.
2. روی «تست Token و پیدا کردن Account ID» بزن.
3. اگر Account ID پیدا شد، همان را استفاده کن.

## Subscription باز نمی‌شود
1. مطمئن شو Worker Deploy شده.
2. Cloudflare → Workers & Pages → worker-name → Visit.
3. انتهای آدرس `/sub` را بزن.
4. همان لینک را داخل نرم‌افزار Paste کن.

## کانفیگ OK پیدا نمی‌شود
1. Timeout را روی 8 یا 10 بگذار.
2. Workers همزمان را کمتر کن؛ مثلاً 16.
3. IP Quality Scanner را اجرا کن.
4. حالت هوشمند یا Clean IP را اجرا کن.
