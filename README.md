<div align="center" dir="rtl">

# CoConection

پنل اتصال هوشمند با رابط کاربری کاملاً مینیمال، استایل خطی، دارک/لایت، فونت وزیرمتن، آیکون‌های SVG داخلی و چیدمان واکنش‌گرا.

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
- **فونت وزیرمتن (Vazirmatn)** — فونت فارسی حرفه‌ای، بارگذاری از Google Fonts
- **تم Dark / Light** — تشخیص تم سیستم + ذخیره انتخاب کاربر در localStorage
- **آیکون‌های SVG داخلی** — تمام آیکون‌ها inline هستند، بدون نیاز به FontAwesome یا Remix
- **موبایل‌محور** — ورودی ۱۶px (بدون زوم)، دکمه‌های ۴۴px، safe-area، چیدمان تک‌ستونه
- **سایدبار ناوبری** — در پنل ادمین، سایدبار با منوی همبرگری برای موبایل
- **صفحات** — داشبورد، لیست کانفیگ‌ها، سازنده کانفیگ محدود، تنظیمات Worker

### سیستم احراز هویت جدید

- **مسیر `/admin/`** — ورود از طریق صفحه لاگین اختصاصی
- **Session Cookie** — احراز هویت با HttpOnly, Secure, SameSite=Strict cookie
- **مقایسه timing-safe** — رمز عبور با روش زمان‌ایمن بررسی می‌شود
- **دکمه خروج** — در سایدبار پنل، با حذف session
- **ریدایرکت خودکار** — `/admin` → `/admin/` (با یا بدون اسلش)

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

- **مقایسه timing-safe** — رمز عبور با روش زمان‌ایمن بررسی می‌شود
- **بدون fallback ناامن** — اگر هیچ متغیر محیطی تنظیم نشده باشد، ایجاد توکن خطا می‌دهد
- **رمز ادمین در URL نیست** — لینک اشتراک محدود از مسیر مستقل استفاده می‌کند
- **اعتبارسنجی payload** — مقادیر quota و expire به‌عنوان اعداد مثبت و متناهی بررسی می‌شوند
- **Session امن** — Cookie با HttpOnly + Secure + SameSite=Strict

---

## فایل‌ها

| فایل | توضیح |
|---|---|
| `worker.js` | **فایل اصلی Worker** — شامل لایه روتینگ UI جدید + منطق اصلی Worker. **این فایل را در Cloudflare دیپلوی کنید.** |
| `Nova System.js` | نسخه قدیمی Worker (بدون روتینگ UI جدید) |
| `Nova Proxy Worker V2 obfuscated.js` | نسخه obfuscated قدیمی |
| `Htmel/index.html` | لندینگ پیج مینیمال — دارک/لایت، SVG، responsive |
| `Htmel/login.html` | صفحه ورود مینیمال |
| `Htmel/panel.html` | پنل ادمین مینیمال — داشبورد، کانفیگ‌ها، سازنده محدود، تنظیمات |
| `Htmel/img/` | اسکرین‌شات‌های پروژه |
| `README.md` | مستندات |

---

## نصب سریع

1. در Cloudflare Workers فایل **`worker.js`** را قرار بدهید. (نه Nova System.js!)
2. متغیرهای لازم پروژه اصلی مثل `PASSWORD`، `UUID`، `KV` و موارد دلخواه را تنظیم کنید.
3. برای مشاهده لندینگ پیج:

```txt
https://YOUR-WORKER.workers.dev/
```

4. برای ورود به پنل مدیریت:

```txt
https://YOUR-WORKER.workers.dev/admin
```

5. رمز عبور Worker خود را وارد کنید (متغیر `PASSWORD` در Cloudflare).
6. در منوی سایدبار، بخش **ساخت کانفیگ محدود** را انتخاب کنید؛ نام، حجم و تعداد روز را وارد کنید و لینک را بسازید.

---

## مسیرها

| مسیر | توضیح |
|---|---|
| `/` | لندینگ پیج |
| `/admin` | ریدایرکت به `/admin/` |
| `/admin/` | صفحه لاگین (اگر احراز هویت نشده) / پنل (اگر احراز شده) |
| `/admin/login` | POST — بررسی رمز عبور |
| `/admin/logout` | خروج و حذف session |
| `/{PASSWORD}/sub` | لینک اشتراک اصلی |
| `/cc-limited-sub/{TOKEN}` | لینک اشتراک محدود |

---

## اعتبار پروژه

- سازنده این نسخه: [M_CODER / mcodersir](https://github.com/mcodersir)
- بیس پروژه: [IRNova/Nova-Proxy](https://github.com/IRNova/Nova-Proxy)
