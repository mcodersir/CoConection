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
- رفع آسیب‌پذیری‌های امنیتی: timing-safe مقایسه HMAC، حذف رمز ادمین از URL اشتراک، اعتبارسنجی دقیق payload
- تولید لینک محدود از مسیر:

```txt
/cc-limited-sub/{TOKEN}
```

این لینک هدر زیر را برای کلاینت‌های سازگار ارسال می‌کند:

```txt
Subscription-Userinfo: upload=0; download=0; total={BYTES}; expire={UNIX_TIME}
Profile-Title: {CONFIG_NAME}
```

> نکته فنی: این قابلیت برای نمایش حجم و انقضا در لینک اشتراک اضافه شده است. محدودسازی واقعی ترافیک در سطح تونل به قابلیت‌های هسته/کلاینت و زیرساخت اجرا وابسته است؛ هسته اصلی Nova-Proxy عمداً دستکاری نشده تا اتصال‌ها خراب نشوند.

---

## فایل‌ها

| فایل | توضیح |
|---|---|
| `Nova System.js` | نسخه اصلی Worker با لایه UI و limited subscription افزوده‌شده |
| `Nova Proxy Worker V2 obfuscated.js` | نسخه obfuscated با همان لایه CoConection |
| `Htmel/index.html` | لندینگ جدید CoConection، کاملاً local و responsive |
| `README.md` | همین مستندات |

---

## نصب سریع

1. در Cloudflare Workers یکی از فایل‌های Worker را قرار بدهید.
2. متغیرهای لازم پروژه اصلی مثل `PASSWORD` یا `ADMIN`، `UUID`، `KV` و موارد دلخواه را تنظیم کنید.
3. وارد مسیر پنل شوید:

```txt
https://YOUR-WORKER/{PASSWORD}/
```

4. در بالای پنل، کارت **ساخت کانفیگ دوم** را می‌بینید؛ نام، حجم و تعداد روز را وارد کنید و لینک را بسازید.

---

## امنیت

- **مقایسه timing-safe**: امضای HMAC با الگوریتم مقایسه زمان‌ایمن بررسی می‌شود تا از حملات timing side-channel جلوگیری شود.
- **بدون secret پیش‌فرض**: اگر هیچ یک از متغیرهای محیطی `KEY`، `PASSWORD`، `ADMIN` یا `UUID` تنظیم نشده باشد، ایجاد توکن با خطا مواجه می‌شود.
- **رمز ادمین در URL نیست**: لینک اشتراک محدود حاوی رمز عبور ادمین نیست و از مسیر مستقل `/cc-limited-sub/` استفاده می‌کند.
- **اعتبارسنجی payload**: مقادیر `quota` و `expire` به‌عنوان اعداد مثبت و متناهی اعتبارسنجی می‌شوند.

---

## اعتبار پروژه

- سازنده این نسخه: [M_CODER / mcodersir](https://github.com/mcodersir)
- بیس پروژه: [IRNova/Nova-Proxy](https://github.com/IRNova/Nova-Proxy)

</div>
