# منابع ادغام‌شده در پروژه

این نرم‌افزار برای کاربر نهایی لینک GitHub باز نمی‌کند. هسته‌های لازم داخل خود پروژه در پوشه `integrated_sources` هستند و UI فقط مسیر Atomic Mail و Cloudflare را باز می‌کند.

## BPB Worker Panel / Wizard

نقش در این پروژه:

- جریان نصب Worker/Pages و ساخت Subscription
- ایده پنل و Subscription برای VLESS/Trojan/Warp
- خروجی سازگار با کلاینت‌های رایج

در این پروژه یک Worker داخلی سبک و BPB-compatible در مسیر زیر قرار دارد:

```text
integrated_sources/BPB_Worker_Panel_Bundle/worker.js
```

## SenPaiScanner

نقش در این پروژه:

- ایده اسکن Endpoint به جای اتکا به ping
- تست HTTP/TLS روی پورت‌های رایج Cloudflare
- ذخیره خروجی Clean IP

هسته داخلی:

```text
integrated_sources/SenPaiScanner_Core/senpai_scanner_core.py
```

## Rasoul v2ray-config-modifier

نقش در این پروژه:

- ایده جایگزینی IP/Endpoint روی کانفیگ‌ها
- تولید گروهی کانفیگ با Clean IP
- اتصال خروجی Scanner به مرحله ساخت کانفیگ

هسته داخلی:

```text
integrated_sources/Rasoul_Config_Modifier/config_modifier_core.py
```

## Cloudflare

Deploy Assistant از Cloudflare API برای نصب Worker داخلی روی اکانت کاربر استفاده می‌کند. کاربر باید API Token معتبر و Account ID درست وارد کند. در v7 نرم‌افزار خطای رایج قرار دادن Token به‌جای Account ID را تشخیص می‌دهد.
