# CoConection

**کانفیگ VPN سالم، تمیز و قابل استفاده فقط با چند کلیک.**

ساخته شده توسط **mcoders** — [github.com/mcodersir](https://github.com/mcodersir)

CoConection یک ابزار شفاف، محلی و متن‌باز است که یک Cloudflare Worker دیپلوی می‌کند، سابسکریپشن‌های BPB را می‌خواند، سلامت endpointها را تست می‌کند، کانفیگ‌های سالم را رتبه‌بندی و خروجی آماده import تولید می‌کند. بدون CDN، بدون کد مبهم، بدون وابستگی خارجی فراتر از stdlib پایتون.

---

## ویژگی‌ها

- **تم دارک/لایت** — با یک کلیک تغییر بده، ترجیح در مرورگر ذخیره می‌شود
- **رابط کاربری خطی مینیمال** — طراحی تمیز با آیکون‌های SVG، بدون فونت یا CSS خارجی
- **گردش کار ۳ مرحله‌ای** — دیپلوی → تست → کپی
- **Nova Easy Mode** — پیش‌اسکن خودکار، رتبه‌بندی بهتر، خروجی آماده import
- **ساخت کانفیگ سفارشی** — کانفیگ اضافی با حجم، زمان و نام دلخواه بساز
- **نمایش زنده نتایج (SSE)** — هر کانفیگ به محض تست نمایش داده می‌شود
- **ذخیره خودکار** — تنظیمات و لیست IPها ذخیره می‌شوند
- **خروجی‌های متنوع** — بهترین کانفیگ، لیست کانفیگ‌های سالم، Clash/Mihomo YAML
- **چند پلتفرمی** — باینری ویندوز، مک و لینوکس
- **بدون وابستگی خارجی** — فقط stdlib پایتون، نیاز به pip install نیست

---

## شروع سریع

### روش ۱: اجرا از سورس

```bash
# کلون
git clone https://github.com/mcodersir/CoConection.git
cd CoConection

# ویندوز
run_windows.bat

# مک/لینوکس
chmod +x run_mac_linux.sh
./run_mac_linux.sh
```

### روش ۲: دانلود باینری

به صفحه [Releases](https://github.com/mcodersir/CoConection/releases) برو و باینری پلتفرم خودت رو دانلود کن:

| پلتفرم | فایل | راهنما |
|---------|------|--------|
| ویندوز | `CoConection-Windows.exe` | دانلود و دابل‌کلیک |
| مک | `CoConection-macOS` | دانلود → `chmod +x CoConection-macOS` → اجرا |
| لینوکس | `CoConection-Linux` | دانلود → `chmod +x CoConection-Linux` → اجرا |

برنامه یک سرور HTTP محلی اجرا می‌کند و مرورگر را خودکار باز می‌کند.

---

## راهنمای استفاده

### مرحله ۱: دیپلوی Worker روی Cloudflare

1. یک حساب رایگان [Cloudflare](https://dash.cloudflare.com/sign-up) بساز
2. به [API Tokens](https://dash.cloudflare.com/profile/api-tokens) برو و یک توکن با دسترسی **Workers Scripts: Edit** بساز
3. توکن API را در مرحله ۱ وارد کن و «تست توکن» را بزن
4. Account ID وارد کن یا اجازه بده خودکار پر شود
5. «ساخت UUID» را بزن تا یک UUID برای VLESS ساخته شود
6. «Deploy Worker» را بزن — اسکریپت Worker روی اکانت تو آپلود می‌شود
7. Subscription URL نمایش‌داده‌شده را کپی کن

### مرحله ۲: گرفتن کانفیگ سالم

1. Subscription URL را Paste کن (یا بعد از دیپلوی خودکار پر می‌شود)
2. حالت را انتخاب کن:
   - **Nova Easy (پیشنهادی)** — IPها را پیش‌اسکن می‌کند، کانفیگ‌ها را تست و رتبه‌بندی می‌کند
   - **Smart** — کانفیگ‌های سابسکریپشن را مستقیم تست می‌کند، در صورت نیاز به Clean IP برمی‌گردد
   - **فقط Clean IP** — فقط با IPهای اسکن‌شده تست می‌کند
3. **Start** را بزن — نتایج زنده را ببین
4. بهترین کانفیگ در مرحله ۴ نمایش داده می‌شود

### مرحله ۳: ساخت کانفیگ سفارشی

1. نامی برای کانفیگ وارد کن (مثلاً "دستگاه-خانگی")
2. حجم را بر حسب GB مشخص کن (0 = نامحدود)
3. زمان انقضا را بر حسب روز مشخص کن (0 = بدون انقضا)
4. پروتکل (VLESS یا Trojan)، پورت و شبکه (WS یا gRPC) را انتخاب کن
5. اختیاریاً یک IP تمیز وارد کن تا به جای دامنه Worker استفاده شود
6. **ساخت کانفیگ سفارشی** را بزن — کانفیگ با تنظیمات تو ساخته می‌شود
7. کپی کن یا به لیست خروجی اضافه کن

### مرحله ۴: کپی و Import

1. بهترین کانفیگ در textarea نمایش داده می‌شود
2. **کپی کانفیگ** را بزن
3. در کلاینتت import کن: Hiddify، NekoBox، v2rayN، Sing-box و غیره

---

## فایل‌های خروجی

همه خروجی‌ها در پوشه `output/` ذخیره می‌شوند:

| فایل | توضیحات |
|------|---------|
| `nova_best_config_only.txt` | بهترین کانفیگ — اول این را import کن |
| `nova_working_configs.txt` | همه کانفیگ‌های سالم به عنوان پشتیبان |
| `nova_quick_import.txt` | بهترین + پشتیبان برای import سریع |
| `nova_clash_meta.yaml` | پروفایل Clash/Mihomo |
| `nova_bundle.json` | نتایج کامل تست و متادیتا |
| `custom_configs.txt` | کانفیگ‌های سفارشی ساخته‌شده |
| `clean_ips.txt` | نتایج اسکن IP سالم |
| `saved_ips.txt` | IPهای ذخیره‌شده برای استفاده بعدی |

---

## تنظیمات پیشرفته

| تنظیم | پیش‌فرض | توضیحات |
|-------|---------|---------|
| Timeout | 7 ثانیه | زمان اتصال به هر endpoint |
| Workers | 48 | تعداد threadهای همزمان |
| Limit | 2600 | حداکثر تعداد کانفیگ برای تست |
| Random IPs | 420 | تعداد IP تصادفی Cloudflare تولیدشده |
| Ports | 443, 8443, 2053, 2083 | پورت‌های TLS برای تست |

---

## معماری

CoConection کاملاً محلی اجرا می‌شود:

- **بکاند**: سرور HTTP stdlib پایتون (`start.py`) — بدون Flask، بدون Django
- **فرانتند**: یک HTML + CSS + JS — بدون CDN، بدون فریمورک
- **Worker**: اسکریپت BPB Worker Panel آپلودشده روی اکانت Cloudflare تو
- **اسکنر**: اسکنر چند فازی endpoint (TCP → TLS → HTTP → WebSocket DPI → Speed)
- **هیچ داده‌ای از کامپیوتر تو خارج نمی‌شود** — همه پردازش محلی است

### ساختار سورس

```
CoConection/
├── start.py              # برنامه اصلی (سرور HTTP + API)
├── cli.py                # رابط خط فرمان
├── src/
│   ├── core.py           # پردازش کانفیگ، اسکن و تست
│   ├── nova_core.py      # رتبه‌بندی و خروجی Nova Easy Mode
│   └── cloudflare_deployer.py  # ارتباط با API کلاودفلر
├── ui/
│   ├── index.html        # رابط کاربری اصلی
│   ├── styles.css        # CSS تم دارک/لایت
│   └── app.js            # منطق فرانتند
├── integrated_sources/
│   ├── BPB_Worker_Panel_Bundle/  # اسکریپت Worker
│   └── Nova_Proxy_Core/         # ادغام Nova
├── docs/                 # مستندات فارسی
├── .github/workflows/    # CI/CD برای ساخت باینری
└── output/               # کانفیگ‌های تولیدشده (در زمان اجرا)
```

---

## تشکر از

- [BPB Worker Panel](https://github.com/bia-pain-bache/BPB-Worker-Panel) — اسکریپت Worker
- [Nova-Proxy](https://github.com/IRNova/Nova-Proxy) — الهام‌بخش Nova Easy Mode
- [SenPaiScanner](https://github.com/MatinSenPai/SenPaiScanner) — روش‌شناسی اسکن
- [v2ray-config-modifier](https://github.com/seramo/v2ray-config-modifier) — رویکرد تغییر کانفیگ

---

## لایسنس

فایل [LICENSE](LICENSE) را ببینید.
