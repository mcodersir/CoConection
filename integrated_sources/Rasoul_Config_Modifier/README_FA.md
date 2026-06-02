# Rasoul Config Modifier Core

این بخش منطق تولید گروهی کانفیگ را داخل برنامه نگه می‌دارد:

1. دریافت کانفیگ پایه از BPB Subscription
2. دریافت Clean IP/Endpoint از Scanner
3. جایگزینی Host/Port با حفظ SNI/Host اصلی
4. ذخیره خروجی در `output/generated_configs.txt`
5. تست و انتخاب بهترین کانفیگ در `output/best_active_config.txt`
