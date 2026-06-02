<div align="center" dir="rtl">

# CoConection

پنل اتصال هوشمند با رابط کاربری کاملاً بازطراحی‌شده، استایل خطی، دارک/لایت، آیکون‌های مینیمال داخلی و چیدمان واکنش‌گرا برای اندروید.

<p>
  <a href="https://github.com/mcodersir">سازنده: M_CODER / mcodersir</a>
  <br>
  <a href="https://github.com/IRNova/Nova-Proxy">Base Project: IRNova/Nova-Proxy</a>
</p>

---

## تغییرات نسخه CoConection

- تغییر نام پروژه و خروجی‌های قابل مشاهده به **CoConection**
- بازطراحی کامل رابط HTML با استایل خطی، ساده و مینیمال
- حذف وابستگی نمایشی به آیکون‌های خارجی و استفاده از آیکون‌های SVG داخلی
- پشتیبانی از تم **Dark / Light** با ذخیره انتخاب کاربر
- بهینه‌سازی چیدمان برای موبایل و اندروید: ورودی ۱۶px، دکمه‌های تاچ، safe-area و grid واکنش‌گرا
- اضافه شدن لایه UI روی صفحات Worker بدون دستکاری هسته اصلی پروکسی
- اضافه شدن سازنده **کانفیگ دوم** با نام، حجم و مدت زمان اختصاصی
- تولید لینک محدود از مسیر:

```txt
/{PASSWORD}/cc-limited-sub/{TOKEN}
```

این لینک هدر زیر را برای کلاینت‌های سازگار ارسال می‌کند:

```txt
Subscription-Userinfo: upload=0; download=0; total={BYTES}; expire={UNIX_TIME}
```

> نکته فنی: این قابلیت برای نمایش حجم و انقضا در لینک اشتراک اضافه شده است. محدودسازی واقعی ترافیک در سطح تونل به قابلیت‌های هسته/کلاینت و زیرساخت اجرا وابسته است؛ هسته اصلی Nova-Proxy عمداً دستکاری نشده تا اتصال‌ها خراب نشوند.

---

## فایل‌ها

| فایل | توضیح |
|---|---|
| `Nova System.js` | نسخه اصلی Worker با لایه UI و limited subscription افزوده‌شده |
| `Nova Proxy Worker V2 obfuscated.js` | نسخه obfuscated با همان لایه CoConection |
| `Htmel/index.html` | لندینگ جدید CoConection، کاملاً local و responsive |
| `README.md` | مستندات فارسی |
| `README_EN.md` | مستندات انگلیسی |

---

## نصب سریع

### ۱) ساخت Worker در Cloudflare

1. وارد [Cloudflare Dashboard](https://dash.cloudflare.com/) شوید.
2. به بخش **Workers & Pages** بروید.
3. روی **Create Worker** بزنید.
4. نام Worker را انتخاب کنید (مثلاً `coconection`).
5. فایل `Nova System.js` یا `Nova Proxy Worker V2 obfuscated.js` را کپی و در ادیتور Worker پیست کنید.
6. روی **Save and Deploy** بزنید.

### ۲) تنظیم Environment Variables

در بخش **Settings → Variables** مقادیر زیر را تنظیم کنید:

| متغیر | الزامی | توضیح |
|---|---|---|
| `PASSWORD` | ✅ بله | رمز ورود به پنل و مسیرهای ادمین |
| `UUID` | ✅ بله | UUID برای VLESS — باید یک UUID معتبر v4 باشد |
| `KEY` | اختیاری | کلید رمزنگاری لینک‌های محدود (حدود ۳۲ کاراکتر تصادفی) |
| `ADMIN` | اختیاری | رمز ادمین جداگانه (اگر تنظیم نشود، `PASSWORD` استفاده می‌شود) |

### ۳) تنظیم KV Namespace (در صورت نیاز)

اگر نسخه اصلی Nova-Proxy از KV استفاده می‌کند:

1. در Cloudflare به **Workers & Pages → KV** بروید.
2. یک Namespace جدید بسازید.
3. در تنظیمات Worker، KV Namespace را با نام `KV` بایند کنید.

### ۴) ورود به پنل

```txt
https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev/{PASSWORD}/
```

در بالای پنل، کارت **ساخت کانفیگ دوم** را می‌بینید؛ نام، حجم و تعداد روز را وارد کنید و لینک را بسازید.

---

## مسیرهای مهم

| مسیر | توضیح |
|---|---|
| `/{PASSWORD}/` | پنل مدیریت |
| `/{PASSWORD}/cc-limited-sub/{TOKEN}` | لینک اشتراک محدود |
| `/{PASSWORD}/__coconection/api/custom-sub` | API ساخت اشتراک محدود (POST) |

---

## اعتبار پروژه

- سازنده این نسخه: [M_CODER / mcodersir](https://github.com/mcodersir)
- بیس پروژه: [IRNova/Nova-Proxy](https://github.com/IRNova/Nova-Proxy)

</div>
