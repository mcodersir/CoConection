# CoConection Changelog

## v2.0.0 — Complete UI Redesign

- **بازطراحی کامل رابط کاربری** — سه صفحه مجزا با استایل مینیمال خطی
- **لندینگ پیج جدید** (`Htmel/index.html`) — hero، ویژگی‌ها، سازنده کانفیگ، تصاویر
- **صفحه ورود جدید** (`Htmel/login.html`) — فرم مینیمال با فیدبک خطا
- **پنل ادمین جدید** (`Htmel/panel.html`) — سایدبار، داشبورد، لیست کانفیگ‌ها، سازنده محدود، تنظیمات
- **صفر وابستگی خارجی** — هیچ CDN، فونت خارجی یا آیکون‌کتابی
- **تم Dark/Light** — تشخیص سیستم + ذخیره انتخاب + تغییر با یک کلیک
- **SVG icons داخلی** — تمام آیکون‌ها inline، بدون نیاز به FontAwesome/Remix
- **موبایل‌محور** — سایدبار همبرگری، ورودی ۱۶px، دکمه‌های ۴۴px، safe-area
- **سازنده کانفیگ محدود** — ایجاد اشتراک با نام، حجم (GB) و مدت (روز) اختصاصی
- **لیست کانفیگ‌ها** — نمایش، کپی و حذف کانفیگ‌های محدود
- **Toast notifications** — پیام‌های موفقیت/خطا به صورت toast

## v1.1.0 — Security Hardening

- **FIX**: Timing-unsafe HMAC signature comparison replaced with constant-time `__ccTimingSafeEqual()` to prevent timing side-channel attacks.
- **FIX**: Hardcoded fallback secret removed — Worker now throws an error if no `KEY`, `PASSWORD`, `ADMIN`, or `UUID` env var is set, instead of falling back to a publicly visible default.
- **FIX**: Admin password no longer embedded in subscription URLs — limited-sub path changed from `/{PASSWORD}/cc-limited-sub/TOKEN` to `/cc-limited-sub/TOKEN`.
- **FIX**: Payload type validation in `__ccReadToken` now checks `q` and `e` as positive finite numbers.
- **ADD**: `Profile-Title` header in limited-sub response for better client display.

## v1.0.0 — Initial CoConection Release

- Rebranded visible UI text from Nova-Proxy to CoConection.
- Added Worker response transformer for a line-style UI without modifying the proxy core.
- Added dark/light theme toggle.
- Added inline local SVG icon replacement for FontAwesome/Remix `<i>` tags.
- Added Android/mobile responsive CSS overrides.
- Added signed limited subscription generator:
  - `/{PASSWORD}/__coconection/api/custom-sub`
  - `/{PASSWORD}/cc-limited-sub/{TOKEN}`
- Rebuilt `Htmel/index.html` as a local, minimal landing page.
- Updated README attribution:
  - Creator: https://github.com/mcodersir
  - Base: https://github.com/IRNova/Nova-Proxy
