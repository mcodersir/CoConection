<div align="center" dir="rtl">

# CoConection

پنل اتصال هوشمند با رابط کاربری کاملاً مینیمال، استایل خطی، دارک/لایت، آیکون‌های SVG داخلی و چیدمان واکنش‌گرا.

<p>
  <a href="https://github.com/mcodersir">سازنده: M_CODER / mcodersir</a>
  <br>
  <a href="https://github.com/IRNova/Nova-Proxy">Base Project: IRNova/Nova-Proxy</a>
</p>

</div>

---

## تغییرات CoConection نسبت به Nova-Proxy اصلی

### رابط کاربری

- **بازطراحی کامل** — سه صفحه مجزا با استایل مینیمال خطی: لندینگ، لاگین، پنل ادمین
- **صفر وابستگی خارجی** — هیچ CDN، فونت خارجی یا آیکون‌کتابی استفاده نشده
- **تم Dark / Light** — تشخیص تم سیستم + ذخیره انتخاب کاربر در localStorage
- **آیکون‌های SVG داخلی** — تمام آیکون‌ها inline هستند، بدون نیاز به FontAwesome یا Remix
- **موبایل‌محور** — ورودی ۱۶px (بدون زوم)، دکمه‌های ۴۴px، safe-area، چیدمان تک‌ستونه
- **سایدبار ناوبری** — در پنل ادمین، سایدبار با منوی همبرگری برای موبایل
- **صفحات** — داشبورد، لیست کانفیگ‌ها، سازنده کانفیگ محدود، تنظیمات Worker

### قابلیت‌های جدید

- **ساخت کانفیگ محدود** — ایجاد اشتراک با حجم (GB) و مدت زمان (روز) اختصاصی
- **لینک اشتراک محدود** از مسیر:

```txt
/cc-limited-sub/{TOKEN}
```

این لینک هدر زیر را برای کلاینت‌های سازگار ارسال می‌کند:

```txt
Subscription-Userinfo: upload=0; download=0; total={BYTES}; expire={UNIX_TIME}
Profile-Title: {CONFIG_NAME}
```

### امنیت

- **مقایسه timing-safe** — امضای HMAC با الگوریتم مقایسه زمان‌ایمن بررسی می‌شود
- **بدون fallback ناامن** — اگر هیچ متغیر محیطی تنظیم نشده باشد، ایجاد توکن خطا می‌دهد
- **رمز ادمین در URL نیست** — لینک اشتراک محدود از مسیر مستقل استفاده می‌کند
- **اعتبارسنجی payload** — مقادیر quota و expire به‌عنوان اعداد مثبت و متناهی بررسی می‌شوند

---

## فایل‌ها

| فایل | توضیح |
|---|---|
| `Nova System.js` | نسخه اصلی Worker با لایه CoConection و limited subscription |
| `Nova Proxy Worker V2 obfuscated.js` | نسخه obfuscated با همان لایه CoConection |
| `Htmel/index.html` | لندینگ پیج مینیمال — دارک/لایت، SVG، responsive |
| `Htmel/login.html` | صفحه ورود مینیمال |
| `Htmel/panel.html` | پنل ادمین مینیمال — داشبورد، کانفیگ‌ها، سازنده محدود، تنظیمات |
| `Htmel/img/` | اسکرین‌شات‌های پروژه |
| `README.md` | مستندات |

---

## نصب سریع

1. در Cloudflare Workers یکی از فایل‌های Worker را قرار بدهید.
2. متغیرهای لازم پروژه اصلی مثل `PASSWORD` یا `ADMIN`، `UUID`، `KV` و موارد دلخواه را تنظیم کنید.
3. وارد مسیر پنل شوید:

```txt
https://YOUR-WORKER/{PASSWORD}/
```

4. در منوی سایدبار، بخش **ساخت کانفیگ محدود** را انتخاب کنید؛ نام، حجم و تعداد روز را وارد کنید و لینک را بسازید.

---

## اعتبار پروژه

- سازنده این نسخه: [M_CODER / mcodersir](https://github.com/mcodersir)
- بیس پروژه: [IRNova/Nova-Proxy](https://github.com/IRNova/Nova-Proxy)
