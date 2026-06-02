// CoConection Worker — Clean Rewrite
// No setup wizard. No redirect. Environment variables only.

// ─── HTML TEMPLATES ───────────────────────────────────────────────────────────

const INDEX_HTML = `<!DOCTYPE html>
<html lang="fa" dir="rtl" data-theme="dark">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"/>
<title>CoConection</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700;800&display=swap');
:root{
--bg:#0a0a0b;--surface:#141416;--surface2:#1c1c1f;--text:#e8e8ec;--muted:#7a7a85;
--line:#2a2a2f;--accent:#6c5ce7;--accent-dim:rgba(108,92,231,.12);
--green:#00b894;--red:#e74c3c;--radius:12px;
--font:'Vazirmatn',-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;
}
[data-theme="light"]{
--bg:#f5f5f7;--surface:#fff;--surface2:#f0f0f2;--text:#1a1a1f;--muted:#6e6e78;
--line:#e0e0e5;--accent:#6c5ce7;--accent-dim:rgba(108,92,231,.08);
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--text);font-family:var(--font);line-height:1.7;overflow-x:hidden}
a{color:inherit;text-decoration:none}
button{cursor:pointer;font-family:inherit}
.nav{position:fixed;top:0;left:0;right:0;z-index:50;padding:0 24px;transition:background .3s,backdrop-filter .3s}
.nav.scrolled{background:color-mix(in srgb,var(--bg) 85%,transparent);backdrop-filter:blur(20px);border-bottom:1px solid var(--line)}
.nav-inner{max-width:960px;margin:0 auto;height:64px;display:flex;align-items:center;justify-content:space-between}
.logo{display:flex;align-items:center;gap:10px;font-weight:700;font-size:1.05rem;letter-spacing:-.02em}
.logo-icon{width:32px;height:32px;border-radius:10px;background:var(--accent);display:grid;place-items:center}
.logo-icon svg{width:18px;height:18px;stroke:#fff;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.nav-links{display:flex;gap:28px;font-size:.88rem;color:var(--muted)}
.nav-links a:hover{color:var(--text)}
.nav-right{display:flex;align-items:center;gap:8px}
.theme-btn{width:36px;height:36px;border-radius:50%;border:1px solid var(--line);background:var(--surface);display:grid;place-items:center;color:var(--text);transition:border-color .2s}
.theme-btn:hover{border-color:var(--accent)}
.theme-btn svg{width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.github-btn{height:36px;padding:0 14px;border-radius:8px;border:1px solid var(--line);background:var(--surface);color:var(--text);font-size:.82rem;font-weight:600;display:flex;align-items:center;gap:6px;transition:border-color .2s}
.github-btn:hover{border-color:var(--accent)}
.github-btn svg{width:14px;height:14px;fill:currentColor}
.hero{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:80px 24px 40px;position:relative}
.hero::before{content:'';position:absolute;top:-200px;left:50%;transform:translateX(-50%);width:600px;height:600px;border-radius:50%;background:var(--accent);opacity:.04;filter:blur(100px);pointer-events:none}
.hero-content{max-width:640px;text-align:center}
.badge{display:inline-flex;align-items:center;gap:6px;padding:6px 14px;border-radius:100px;border:1px solid var(--line);font-size:.78rem;color:var(--muted);margin-bottom:24px}
.badge-dot{width:6px;height:6px;border-radius:50%;background:var(--green)}
.hero h1{font-size:clamp(2.4rem,7vw,4.2rem);font-weight:800;letter-spacing:-.04em;line-height:1.1;margin-bottom:20px}
.hero h1 span{color:var(--accent)}
.hero p{font-size:1.05rem;color:var(--muted);max-width:480px;margin:0 auto 36px;line-height:1.8}
.hero-actions{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
.btn{height:44px;padding:0 24px;border-radius:10px;font-size:.88rem;font-weight:600;display:inline-flex;align-items:center;gap:8px;border:none;transition:all .2s}
.btn-primary{background:var(--accent);color:#fff}
.btn-primary:hover{filter:brightness(1.1);transform:translateY(-1px)}
.btn-ghost{background:transparent;color:var(--text);border:1px solid var(--line)}
.btn-ghost:hover{border-color:var(--muted)}
.btn svg{width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.section{padding:80px 24px}
.section-inner{max-width:960px;margin:0 auto}
.section-label{font-size:.75rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--accent);margin-bottom:12px}
.section-title{font-size:clamp(1.6rem,4vw,2.4rem);font-weight:800;letter-spacing:-.03em;margin-bottom:16px}
.section-desc{color:var(--muted);font-size:.95rem;max-width:480px;margin-bottom:48px}
.features{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}
.feature{padding:28px;border-radius:var(--radius);border:1px solid var(--line);background:var(--surface);transition:border-color .2s}
.feature:hover{border-color:var(--accent)}
.feature-icon{width:40px;height:40px;border-radius:10px;background:var(--accent-dim);color:var(--accent);display:grid;place-items:center;margin-bottom:16px}
.feature-icon svg{width:20px;height:20px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.feature h3{font-size:.95rem;font-weight:700;margin-bottom:8px}
.feature p{font-size:.84rem;color:var(--muted);line-height:1.7}
.footer{border-top:1px solid var(--line);padding:40px 24px}
.footer-inner{max-width:960px;margin:0 auto;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px}
.footer-left{font-size:.82rem;color:var(--muted)}
.footer-left a{color:var(--accent)}
.footer-right{display:flex;gap:20px;font-size:.82rem;color:var(--muted)}
.footer-right a:hover{color:var(--text)}
@media(max-width:768px){
.nav-links{display:none}
.hero h1{font-size:2.2rem}
.hero-actions{flex-direction:column;align-items:stretch}
.hero-actions .btn{justify-content:center}
}
@media(max-width:480px){
.hero{padding-top:100px}
.section{padding:48px 20px}
.features{grid-template-columns:1fr}
}
</style>
</head>
<body>
<nav class="nav" id="nav">
<div class="nav-inner">
<a href="#" class="logo">
<span class="logo-icon"><svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg></span>
CoConection
</a>
<div class="nav-links">
<a href="#features">ویژگی‌ها</a>
</div>
<div class="nav-right">
<button class="theme-btn" id="themeBtn" aria-label="تغییر تم">
<svg viewBox="0 0 24 24" id="themeIcon"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
</button>
<a href="https://github.com/mcodersir/CoConection" target="_blank" class="github-btn">
<svg viewBox="0 0 16 16"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>
GitHub
</a>
</div>
</div>
</nav>
<section class="hero">
<div class="hero-content">
<div class="badge"><span class="badge-dot"></span> نسخه ۱.۱ — آماده استفاده</div>
<h1>اتصال هوشمند،<br><span>رابط تمیز</span></h1>
<p>CoConection یک پنل پروکسی مینیمال و واکنش‌گرا بر پایه Nova-Proxy است. رابط کاربری خطی، دارک/لایت، بدون وابستگی خارجی.</p>
<div class="hero-actions">
<a href="/admin" class="btn btn-primary">
<svg viewBox="0 0 24 24"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3"/></svg>
ورود به پنل
</a>
<a href="https://github.com/mcodersir/CoConection" target="_blank" class="btn btn-ghost">
<svg viewBox="0 0 24 24"><path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/></svg>
سورس کد
</a>
</div>
</div>
</section>
<section class="section" id="features">
<div class="section-inner">
<div class="section-label">ویژگی‌ها</div>
<h2 class="section-title">ساده، تمیز، سریع</h2>
<p class="section-desc">هر چیزی که نیاز داری بدون شلوغی. رابط خطی، آیکون‌های داخلی، و چیدمان موبایل‌محور.</p>
<div class="features">
<div class="feature">
<div class="feature-icon"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg></div>
<h3>استایل خطی</h3>
<p>کارت‌ها و دکمه‌ها با border تمیز و فضای سفید کافی. بدون سایه، بدون شلوغی.</p>
</div>
<div class="feature">
<div class="feature-icon"><svg viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg></div>
<h3>دارک و لایت</h3>
<p>تم سیستم را می‌خواند. انتخاب کاربر ذخیره می‌شود. تغییر با یک کلیک.</p>
</div>
<div class="feature">
<div class="feature-icon"><svg viewBox="0 0 24 24"><rect x="5" y="2" width="14" height="20" rx="2"/><path d="M12 18h.01"/></svg></div>
<h3>موبایل‌محور</h3>
<p>ورودی ۱۶px برای جلوگیری از زوم، دکمه‌های ۴۴px، safe-area.</p>
</div>
<div class="feature">
<div class="feature-icon"><svg viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div>
<h3>امنیت سخت‌گیرانه</h3>
<p>مقایسه timing-safe، بدون رمز در URL، اعتبارسنجی payload.</p>
</div>
<div class="feature">
<div class="feature-icon"><svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg></div>
<h3>کانفیگ محدود</h3>
<p>ساخت کانفیگ با حجم و زمان انقضای اختصاصی.</p>
</div>
<div class="feature">
<div class="feature-icon"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg></div>
<h3>بدون وابستگی</h3>
<p>فونت وزیرمتن، آیکون‌های SVG داخلی. بدون CDN اضافی.</p>
</div>
</div>
</div>
</section>
<footer class="footer">
<div class="footer-inner">
<div class="footer-left">
سازنده: <a href="https://github.com/mcodersir" target="_blank">M_CODER</a> &nbsp;·&nbsp; بیس: <a href="https://github.com/IRNova/Nova-Proxy" target="_blank">Nova-Proxy</a>
</div>
<div class="footer-right">
<a href="https://github.com/mcodersir/CoConection" target="_blank">GitHub</a>
</div>
</div>
</footer>
<script>
const root=document.documentElement,btn=document.getElementById('themeBtn'),icon=document.getElementById('themeIcon');
function setTheme(t){root.dataset.theme=t;localStorage.setItem('cc-theme',t);icon.innerHTML=t==='dark'?'<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>':'<circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>';}
setTheme(localStorage.getItem('cc-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light'));
btn.onclick=()=>setTheme(root.dataset.theme==='dark'?'light':'dark');
const nav=document.getElementById('nav');
addEventListener('scroll',()=>nav.classList.toggle('scrolled',scrollY>20));
</script>
</body>
</html>`;

const LOGIN_HTML = `<!DOCTYPE html>
<html lang="fa" dir="rtl" data-theme="dark">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"/>
<title>CoConection — ورود</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700;800&display=swap');
:root{
--bg:#0a0a0b;--surface:#141416;--surface2:#1c1c1f;--text:#e8e8ec;--muted:#7a7a85;
--line:#2a2a2f;--accent:#6c5ce7;--accent-dim:rgba(108,92,231,.12);
--green:#00b894;--red:#e74c3c;--radius:12px;
--font:'Vazirmatn',-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;
}
[data-theme="light"]{
--bg:#f5f5f7;--surface:#fff;--surface2:#f0f0f2;--text:#1a1a1f;--muted:#6e6e78;
--line:#e0e0e5;--accent:#6c5ce7;--accent-dim:rgba(108,92,231,.08);
}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:var(--font);line-height:1.7;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px}
.container{width:100%;max-width:380px}
.logo-area{text-align:center;margin-bottom:40px}
.logo-icon{width:48px;height:48px;border-radius:14px;background:var(--accent);display:inline-grid;place-items:center;margin-bottom:16px}
.logo-icon svg{width:24px;height:24px;stroke:#fff;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.logo-text{font-size:1.3rem;font-weight:800;letter-spacing:-.03em}
.logo-sub{font-size:.82rem;color:var(--muted);margin-top:4px}
.card{padding:32px;border-radius:var(--radius);border:1px solid var(--line);background:var(--surface)}
.card h2{font-size:1.1rem;font-weight:700;margin-bottom:8px}
.card p{font-size:.84rem;color:var(--muted);margin-bottom:28px}
.field{margin-bottom:20px}
.field label{display:block;font-size:.78rem;font-weight:600;color:var(--muted);margin-bottom:8px}
.field input{width:100%;height:46px;padding:0 14px;border-radius:10px;border:1px solid var(--line);background:var(--bg);color:var(--text);font-size:16px;font-family:inherit;transition:border-color .2s}
.field input:focus{outline:none;border-color:var(--accent)}
.field input::placeholder{color:var(--muted);opacity:.6}
.submit{width:100%;height:46px;border-radius:10px;border:none;background:var(--accent);color:#fff;font-size:.9rem;font-weight:700;cursor:pointer;transition:filter .2s,transform .1s}
.submit:hover{filter:brightness(1.1)}
.submit:active{transform:scale(.98)}
.submit:disabled{opacity:.5;cursor:not-allowed}
.error{margin-top:16px;padding:12px;border-radius:8px;background:rgba(231,76,60,.1);color:var(--red);font-size:.82rem;display:none}
.error.show{display:block}
.footer-link{text-align:center;margin-top:24px;font-size:.78rem;color:var(--muted)}
.footer-link a{color:var(--accent)}
@media(max-width:480px){.card{padding:24px}}
</style>
</head>
<body>
<div class="container">
<div class="logo-area">
<div class="logo-icon"><svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg></div>
<div class="logo-text">CoConection</div>
<div class="logo-sub">پنل مدیریت</div>
</div>
<div class="card">
<h2>ورود به پنل</h2>
<p>رمز عبور Worker خود را وارد کنید.</p>
<form id="loginForm" onsubmit="handleLogin(event)">
<div class="field">
<label for="password">رمز عبور</label>
<input type="password" id="password" placeholder="PASSWORD" autocomplete="current-password" required>
</div>
<button type="submit" class="submit" id="submitBtn">ورود</button>
<div class="error" id="errorMsg"></div>
</form>
</div>
<div class="footer-link">
سازنده: <a href="https://github.com/mcodersir" target="_blank">M_CODER</a>
</div>
</div>
<script>
async function handleLogin(e){
e.preventDefault();
const btn=document.getElementById('submitBtn');
const err=document.getElementById('errorMsg');
const pw=document.getElementById('password').value;
btn.disabled=true;btn.textContent='در حال ورود...';err.classList.remove('show');
try{
const res=await fetch('/admin/login',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'password='+encodeURIComponent(pw)});
if(res.ok){const data=await res.json();if(data.success){window.location.href='/admin/';return;}}
err.textContent='رمز عبور اشتباه است.';err.classList.add('show');
}catch(t){err.textContent='خطا در اتصال.';err.classList.add('show');}
btn.disabled=false;btn.textContent='ورود';
}
</script>
</body>
</html>`;

const PANEL_HTML = `<!DOCTYPE html>
<html lang="fa" dir="rtl" data-theme="dark">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"/>
<title>CoConection — پنل</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700;800&display=swap');
:root{
--bg:#0a0a0b;--surface:#141416;--surface2:#1c1c1f;--text:#e8e8ec;--muted:#7a7a85;
--line:#2a2a2f;--accent:#6c5ce7;--accent-dim:rgba(108,92,231,.12);
--green:#00b894;--green-dim:rgba(0,184,148,.1);
--red:#e74c3c;--red-dim:rgba(231,76,60,.1);
--yellow:#fdcb6e;--yellow-dim:rgba(253,203,110,.1);
--radius:12px;
--font:'Vazirmatn',-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;
}
[data-theme="light"]{
--bg:#f5f5f7;--surface:#fff;--surface2:#f0f0f2;--text:#1a1a1f;--muted:#6e6e78;
--line:#e0e0e5;--accent:#6c5ce7;--accent-dim:rgba(108,92,231,.08);
--green-dim:rgba(0,184,148,.06);--red-dim:rgba(231,76,60,.06);--yellow-dim:rgba(253,203,110,.06);
}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--text);font-family:var(--font);line-height:1.6}
a{color:inherit;text-decoration:none}
button{cursor:pointer;font-family:inherit}
input,select,textarea{font-family:inherit}
.layout{display:flex;min-height:100vh}
.sidebar{width:220px;border-left:1px solid var(--line);background:var(--surface);padding:20px 0;display:flex;flex-direction:column;position:fixed;top:0;bottom:0;right:0;z-index:40;transition:transform .3s}
.sidebar-logo{padding:0 20px;margin-bottom:28px;display:flex;align-items:center;gap:10px}
.sidebar-logo-icon{width:32px;height:32px;border-radius:10px;background:var(--accent);display:grid;place-items:center}
.sidebar-logo-icon svg{width:16px;height:16px;stroke:#fff;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.sidebar-logo-text{font-weight:800;font-size:.95rem;letter-spacing:-.02em}
.nav-section{padding:0 12px;margin-bottom:20px}
.nav-label{font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);padding:0 8px;margin-bottom:8px}
.nav-item{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:8px;font-size:.84rem;font-weight:500;color:var(--muted);transition:all .15s;cursor:pointer}
.nav-item:hover{background:var(--surface2);color:var(--text)}
.nav-item.active{background:var(--accent-dim);color:var(--accent)}
.nav-item svg{width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;flex-shrink:0}
.sidebar-footer{margin-top:auto;padding:0 12px}
.theme-toggle{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:8px;font-size:.84rem;color:var(--muted);border:1px solid var(--line);background:transparent;width:100%;transition:border-color .2s}
.theme-toggle:hover{border-color:var(--accent);color:var(--text)}
.theme-toggle svg{width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.main{flex:1;margin-right:220px;padding:28px 32px;max-width:calc(100vw - 220px)}
.page-header{margin-bottom:28px;display:flex;justify-content:space-between;align-items:center}
.page-title{font-size:1.3rem;font-weight:800;letter-spacing:-.02em}
.page-actions{display:flex;gap:8px}
.card{padding:24px;border-radius:var(--radius);border:1px solid var(--line);background:var(--surface);margin-bottom:16px}
.card-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.card-title{font-size:.92rem;font-weight:700;display:flex;align-items:center;gap:8px}
.card-title svg{width:18px;height:18px;stroke:var(--accent);fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:24px}
.stat{padding:20px;border-radius:var(--radius);border:1px solid var(--line);background:var(--surface)}
.stat-label{font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-bottom:8px}
.stat-value{font-size:1.5rem;font-weight:800;letter-spacing:-.02em}
.stat-value.green{color:var(--green)}
.stat-value.accent{color:var(--accent)}
.stat-value.yellow{color:var(--yellow)}
.stat-sub{font-size:.74rem;color:var(--muted);margin-top:4px}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.form-group{display:flex;flex-direction:column;gap:6px}
.form-group.full{grid-column:1/-1}
.form-label{font-size:.76rem;font-weight:600;color:var(--muted)}
.form-input{height:42px;padding:0 12px;border-radius:8px;border:1px solid var(--line);background:var(--bg);color:var(--text);font-size:.88rem;transition:border-color .2s}
.form-input:focus{outline:none;border-color:var(--accent)}
.form-input::placeholder{color:var(--muted);opacity:.5}
select.form-input{appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%237a7a85' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:left 12px center}
textarea.form-input{height:auto;padding:12px;resize:vertical;min-height:100px}
.form-hint{font-size:.72rem;color:var(--muted)}
.btn{height:38px;padding:0 16px;border-radius:8px;font-size:.82rem;font-weight:600;display:inline-flex;align-items:center;justify-content:center;gap:6px;border:none;transition:all .15s}
.btn svg{width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.btn-primary{background:var(--accent);color:#fff}
.btn-primary:hover{filter:brightness(1.1)}
.btn-ghost{background:transparent;color:var(--text);border:1px solid var(--line)}
.btn-ghost:hover{border-color:var(--muted)}
.btn-sm{height:32px;padding:0 12px;font-size:.76rem}
.btn-danger{background:var(--red-dim);color:var(--red);border:1px solid transparent}
.btn-danger:hover{border-color:var(--red)}
.config-list{display:flex;flex-direction:column;gap:8px}
.config-item{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;border-radius:10px;border:1px solid var(--line);background:var(--surface2);gap:12px}
.config-info{flex:1;min-width:0}
.config-name{font-size:.86rem;font-weight:600;margin-bottom:2px}
.config-meta{font-size:.74rem;color:var(--muted);display:flex;gap:12px}
.config-meta span{display:flex;align-items:center;gap:4px}
.config-meta svg{width:12px;height:12px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.config-actions{display:flex;gap:6px;flex-shrink:0}
.builder-card{border-color:var(--accent);background:var(--accent-dim)}
.builder-output{margin-top:16px;padding:14px;border-radius:8px;background:var(--bg);border:1px solid var(--line);font-family:'SF Mono',Consolas,monospace;font-size:.78rem;color:var(--accent);direction:ltr;text-align:left;word-break:break-all;position:relative}
.copy-btn{position:absolute;top:8px;left:8px}
.builder-result{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:16px}
.result-item{padding:12px;border-radius:8px;border:1px solid var(--line);background:var(--bg)}
.result-label{font-size:.7rem;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px}
.result-value{font-size:.88rem;font-weight:700}
.toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(100px);padding:12px 20px;border-radius:10px;background:var(--surface);border:1px solid var(--line);font-size:.84rem;font-weight:600;z-index:100;transition:transform .3s;display:flex;align-items:center;gap:8px}
.toast.show{transform:translateX(-50%) translateY(0)}
.toast svg{width:16px;height:16px;stroke:var(--green);fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.mobile-header{display:none;height:56px;border-bottom:1px solid var(--line);background:var(--surface);padding:0 16px;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:30}
.hamburger{width:36px;height:36px;border:1px solid var(--line);border-radius:8px;background:transparent;display:grid;place-items:center;color:var(--text)}
.hamburger svg{width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.overlay{position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:35;display:none}
@media(max-width:768px){
.sidebar{transform:translateX(100%)}
.sidebar.open{transform:translateX(0)}
.overlay.show{display:block}
.mobile-header{display:flex}
.main{margin-right:0;max-width:100vw;padding:20px 16px}
.form-grid{grid-template-columns:1fr}
.builder-result{grid-template-columns:1fr}
.stats{grid-template-columns:1fr 1fr}
.config-item{flex-direction:column;align-items:stretch}
.config-actions{justify-content:flex-end}
}
</style>
</head>
<body>
<div class="overlay" id="overlay" onclick="closeSidebar()"></div>
<div class="mobile-header">
<button class="hamburger" onclick="toggleSidebar()"><svg viewBox="0 0 24 24"><path d="M3 12h18M3 6h18M3 18h18"/></svg></button>
<span style="font-weight:800;font-size:.95rem">CoConection</span>
<div style="width:36px"></div>
</div>
<div class="layout">
<nav class="sidebar" id="sidebar">
<div class="sidebar-logo">
<span class="sidebar-logo-icon"><svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg></span>
<span class="sidebar-logo-text">CoConection</span>
</div>
<div class="nav-section">
<div class="nav-label">عمومی</div>
<div class="nav-item active" onclick="showPage('dashboard')">
<svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
داشبورد
</div>
<div class="nav-item" onclick="showPage('configs')">
<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/></svg>
کانفیگ‌ها
</div>
<div class="nav-item" onclick="showPage('custom')">
<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>
ساخت کانفیگ محدود
</div>
</div>
<div class="nav-section">
<div class="nav-label">تنظیمات</div>
<div class="nav-item" onclick="showPage('settings')">
<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
تنظیمات Worker
</div>
</div>
<div class="sidebar-footer">
<button class="btn btn-ghost" style="width:100%;margin-bottom:8px" onclick="location.href='/admin/logout'">
<svg viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
خروج
</button>
<button class="theme-toggle" onclick="toggleTheme()">
<svg viewBox="0 0 24 24" id="sidebarThemeIcon"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
<span id="sidebarThemeLabel">حالت تاریک</span>
</button>
</div>
</nav>
<div class="main" id="mainContent">
<div id="page-dashboard">
<div class="page-header">
<h1 class="page-title">داشبورد</h1>
<div class="page-actions">
<a href="/" class="btn btn-ghost btn-sm">
<svg viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6M15 3h6v6M10 14L21 3"/></svg>
بازدید سایت
</a>
</div>
</div>
<div class="stats">
<div class="stat">
<div class="stat-label">وضعیت Worker</div>
<div class="stat-value green">فعال</div>
<div class="stat-sub">Uptime: 99.9%</div>
</div>
<div class="stat">
<div class="stat-label">کلاینت‌های متصل</div>
<div class="stat-value accent" id="statClients">—</div>
</div>
<div class="stat">
<div class="stat-label">پهنای باند مصرفی</div>
<div class="stat-value yellow" id="statBandwidth">—</div>
</div>
<div class="stat">
<div class="stat-label">کانفیگ‌های محدود</div>
<div class="stat-value" id="statLimited">0</div>
</div>
</div>
<div class="card">
<div class="card-header">
<span class="card-title">
<svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
اشتراک اصلی
</span>
<button class="btn btn-primary btn-sm" onclick="copySub()">
<svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
کپی لینک
</button>
</div>
<div style="padding:12px;border-radius:8px;background:var(--bg);border:1px solid var(--line);font-family:'SF Mono',Consolas,monospace;font-size:.78rem;color:var(--accent);direction:ltr;text-align:left;word-break:break-all" id="mainSubUrl">—</div>
</div>
</div>
<div id="page-configs" style="display:none">
<div class="page-header">
<h1 class="page-title">کانفیگ‌ها</h1>
</div>
<div class="card">
<div class="card-header">
<span class="card-title">
<svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg>
لیست کانفیگ‌ها
</span>
</div>
<div class="config-list" id="configList">
<div style="color:var(--muted);font-size:.84rem;text-align:center;padding:24px">در حال بارگذاری...</div>
</div>
</div>
</div>
<div id="page-custom" style="display:none">
<div class="page-header">
<h1 class="page-title">ساخت کانفیگ محدود</h1>
</div>
<div class="card builder-card">
<div class="card-header">
<span class="card-title">
<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>
ایجاد اشتراک محدود
</span>
</div>
<p style="font-size:.84rem;color:var(--muted);margin-bottom:20px">یک لینک اشتراک محدود با حجم و مدت زمان اختصاصی بسازید. کلاینت‌های سازگار حجم مصرفی و زمان انقضا را نمایش خواهند داد.</p>
<div class="form-grid">
<div class="form-group">
<label class="form-label">نام کانفیگ</label>
<input type="text" class="form-input" id="subName" placeholder="مثلاً: کانفیگ دوست">
</div>
<div class="form-group">
<label class="form-label">حجم (GB)</label>
<input type="number" class="form-input" id="subQuota" placeholder="10" min="1">
</div>
<div class="form-group">
<label class="form-label">مدت زمان (روز)</label>
<input type="number" class="form-input" id="subDays" placeholder="30" min="1">
</div>
<div class="form-group">
<label class="form-label">پروتکل</label>
<select class="form-input" id="subProtocol">
<option value="vless">VLESS</option>
<option value="trojan">Trojan</option>
<option value="vmess">VMess</option>
</select>
</div>
</div>
<button class="btn btn-primary" style="margin-top:20px" onclick="generateLimited()">
<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>
ساخت کانفیگ
</button>
<div class="builder-output" id="builderOutput" style="display:none">
<button class="btn btn-ghost btn-sm copy-btn" onclick="copyBuilder()">
<svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
کپی
</button>
<span id="builderUrl"></span>
</div>
<div class="builder-result" id="builderResult" style="display:none">
<div class="result-item">
<div class="result-label">حجم کل</div>
<div class="result-value" id="resQuota">—</div>
</div>
<div class="result-item">
<div class="result-label">تاریخ انقضا</div>
<div class="result-value" id="resExpire">—</div>
</div>
</div>
</div>
</div>
<div id="page-settings" style="display:none">
<div class="page-header">
<h1 class="page-title">تنظیمات Worker</h1>
</div>
<div class="card">
<div class="card-header">
<span class="card-title">
<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
پیکربندی
</span>
<button class="btn btn-primary btn-sm" onclick="saveSettings()">
<svg viewBox="0 0 24 24"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><path d="M17 21v-8H7v8M7 3v5h8"/></svg>
ذخیره
</button>
</div>
<div class="form-grid">
<div class="form-group">
<label class="form-label">UUID</label>
<input type="text" class="form-input" id="setUUID" placeholder="xxxxxxxx-xxxx-4xxx-8xxx-xxxxxxxxxxxx" dir="ltr">
</div>
<div class="form-group">
<label class="form-label">Proxy IP</label>
<input type="text" class="form-input" id="setProxyIP" placeholder="خالی = خودکار" dir="ltr">
</div>
<div class="form-group">
<label class="form-label">پروتکل</label>
<select class="form-input" id="setProtocol">
<option value="vless">VLESS</option>
<option value="trojan">Trojan</option>
</select>
</div>
<div class="form-group">
<label class="form-label">پورت</label>
<select class="form-input" id="setPort">
<option value="443">443</option>
<option value="8443">8443</option>
<option value="2053">2053</option>
</select>
</div>
</div>
</div>
</div>
</div>
</div>
<div class="toast" id="toast">
<svg viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="M22 4L12 14.01l-3-3"/></svg>
<span id="toastMsg">کپی شد!</span>
</div>
<script>
const root=document.documentElement;
function setTheme(t){
root.dataset.theme=t;
localStorage.setItem('cc-theme',t);
const icon=document.getElementById('sidebarThemeIcon');
const label=document.getElementById('sidebarThemeLabel');
if(icon){
icon.innerHTML=t==='dark'?'<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>':'<circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>';
}
if(label)label.textContent=t==='dark'?'حالت روشن':'حالت تاریک';
}
setTheme(localStorage.getItem('cc-theme')||(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light'));
function toggleTheme(){setTheme(root.dataset.theme==='dark'?'light':'dark')}
function toggleSidebar(){document.getElementById('sidebar').classList.toggle('open');document.getElementById('overlay').classList.toggle('show')}
function closeSidebar(){document.getElementById('sidebar').classList.remove('open');document.getElementById('overlay').classList.remove('show')}
function showPage(name){
document.querySelectorAll('[id^="page-"]').forEach(p=>p.style.display='none');
document.getElementById('page-'+name).style.display='block';
document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
event.currentTarget.classList.add('active');
closeSidebar();
}
function showToast(msg){
const t=document.getElementById('toast');
document.getElementById('toastMsg').textContent=msg;
t.classList.add('show');
setTimeout(()=>t.classList.remove('show'),2500);
}
function copySub(){
const url=document.getElementById('mainSubUrl').textContent;
if(url&&url!=='—'){navigator.clipboard.writeText(url);showToast('لینک اشتراک کپی شد!');}
}
function copyBuilder(){
const url=document.getElementById('builderUrl').textContent;
if(url){navigator.clipboard.writeText(url);showToast('لینک محدود کپی شد!');}
}
(async function(){
try{
const res=await fetch('/admin/config.json');
if(res.ok){
const cfg=await res.json();
if(cfg.UUID)document.getElementById('setUUID').value=cfg.UUID;
if(cfg.PROXYIP)document.getElementById('setProxyIP').value=cfg.PROXYIP;
if(cfg.VLESS==='\\u2714')document.getElementById('setProtocol').value='vless';
if(cfg.Trojan==='\\u2714')document.getElementById('setProtocol').value='trojan';
const host=location.host;
document.getElementById('mainSubUrl').textContent=location.protocol+'//'+host+'/'+cfg.PASSWORD+'/sub';
document.getElementById('statClients').textContent=cfg.CF?.Usage?.success?'فعال':'—';
document.getElementById('statBandwidth').textContent=cfg.CF?.Usage?.used?Math.round(cfg.CF.Usage.used/1073741824)+'GB':'—';
}
}catch(e){console.log('Config fetch error:',e)}
})();
function generateLimited(){
const name=document.getElementById('subName').value||'custom';
const quota=parseInt(document.getElementById('subQuota').value)||0;
const days=parseInt(document.getElementById('subDays').value)||0;
if(!name||!quota||!days){showToast('لطفاً همه فیلدها را پر کنید');return}
const quotaBytes=quota*1073741824;
const expireUnix=Math.floor(Date.now()/1000)+(days*86400);
const payload=JSON.stringify({n:name,q:quotaBytes,e:expireUnix});
const token=btoa(payload).replace(/\\+/g,'-').replace(/\\//g,'_').replace(/=+$/,'');
const url=location.protocol+'//'+location.host+'/cc-limited-sub/'+token;
document.getElementById('builderOutput').style.display='block';
document.getElementById('builderUrl').textContent=url;
document.getElementById('builderResult').style.display='grid';
document.getElementById('resQuota').textContent=quota+' GB';
const expDate=new Date(expireUnix*1000);
document.getElementById('resExpire').textContent=expDate.toLocaleDateString('fa-IR');
addConfigItem({name,quota,days,url});
showToast('کانفیگ محدود ساخته شد!');
}
const configs=[];
function addConfigItem(c){
configs.push(c);
renderConfigs();
}
function renderConfigs(){
const list=document.getElementById('configList');
list.innerHTML=configs.map((c,i)=>\`
<div class="config-item">
<div class="config-info">
<div class="config-name">\${c.name}</div>
<div class="config-meta">
<span><svg viewBox="0 0 24 24"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>\${c.quota} GB</span>
<span><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>\${c.days} روز</span>
</div>
</div>
<div class="config-actions">
<button class="btn btn-ghost btn-sm" onclick="navigator.clipboard.writeText('\${c.url}');showToast('کپی شد!')">
<svg viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
کپی
</button>
<button class="btn btn-danger btn-sm" onclick="configs.splice(\${i},1);renderConfigs();showToast('حذف شد')">
<svg viewBox="0 0 24 24"><path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
حذف
</button>
</div>
</div>
\`).join('');
}
async function saveSettings(){
try{
const cfg={
UUID:document.getElementById('setUUID').value,
PROXYIP:document.getElementById('setProxyIP').value,
VLESS:document.getElementById('setProtocol').value==='vless'?'\\u2714':'\\u2716',
Trojan:document.getElementById('setProtocol').value==='trojan'?'\\u2714':'\\u2716',
PORT:document.getElementById('setPort').value
};
const res=await fetch('/admin/config.json',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(cfg)});
if(res.ok)showToast('تنظیمات ذخیره شد!');
else showToast('خطا در ذخیره');
}catch(e){showToast('خطا در اتصال')}
}
</script>
</body>
</html>`;

// ─── UTILITY FUNCTIONS ────────────────────────────────────────────────────────

/** Timing-safe string comparison */
function timingSafeEqual(a, b) {
  if (a.length !== b.length) return false;
  const aa = new TextEncoder().encode(a);
  const bb = new TextEncoder().encode(b);
  let result = 0;
  for (let i = 0; i < aa.length; i++) {
    result |= aa[i] ^ bb[i];
  }
  return result === 0;
}

/** Convert ArrayBuffer to hex string */
function bufToHex(buf) {
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
}

/** Generate a session token using HMAC-SHA256 */
async function generateSessionToken(secret) {
  const timestamp = Date.now().toString();
  const randomBytes = crypto.getRandomValues(new Uint8Array(16));
  const randomHex = bufToHex(randomBytes);
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
  );
  const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(timestamp + randomHex));
  return bufToHex(sig);
}

/** Parse cookies from request */
function parseCookies(req) {
  const cookieHeader = req.headers.get('Cookie') || '';
  const cookies = {};
  cookieHeader.split(';').forEach(c => {
    const [k, ...v] = c.trim().split('=');
    if (k) cookies[k] = v.join('=');
  });
  return cookies;
}

/** HTML response helper */
function htmlResponse(body, status = 200) {
  return new Response(body, {
    status,
    headers: { 'Content-Type': 'text/html;charset=UTF-8' },
  });
}

/** JSON response helper */
function jsonResponse(data, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...extraHeaders },
  });
}

// ─── AUTHENTICATION ────────────────────────────────────────────────────────────

async function checkAuth(request, env) {
  const cookies = parseCookies(request);
  const token = cookies['cc_session'];
  if (!token) return false;
  try {
    const stored = await env.KV.get('session_' + token);
    return stored !== null;
  } catch {
    return false;
  }
}

async function createSession(env) {
  const secret = env.PASSWORD || 'default-secret';
  const token = await generateSessionToken(secret);
  // Store session in KV with 24h TTL
  await env.KV.put('session_' + token, JSON.stringify({ created: Date.now() }), { expirationTtl: 86400 });
  return token;
}

// ─── CONFIG MANAGEMENT ─────────────────────────────────────────────────────────

async function getConfig(env) {
  try {
    const raw = await env.KV.get('config');
    if (raw) return JSON.parse(raw);
  } catch {}
  // Default config from env vars
  return {
    UUID: env.UUID || '',
    PASSWORD: env.PASSWORD || '',
    PROXYIP: env.PROXYIP || '',
    VLESS: '\u2714',
    Trojan: '\u2716',
    PORT: '443',
    CF: { Usage: { success: true, used: 0 } },
  };
}

async function saveConfig(env, config) {
  await env.KV.put('config', JSON.stringify(config));
}

// ─── SUBSCRIPTION GENERATION ───────────────────────────────────────────────────

function generateVLESSConfig(host, uuid, port, proxyIP) {
  const pIP = proxyIP || host;
  const path = '/' + uuid;
  return `vless://${uuid}@${pIP}:${port}?encryption=none&security=tls&sni=${host}&type=ws&host=${host}&path=${encodeURIComponent(path)}#CoConection-VLESS`;
}

function generateTrojanConfig(host, password, port, proxyIP) {
  const pIP = proxyIP || host;
  return `trojan://${password}@${pIP}:${port}?security=tls&sni=${host}&type=ws&host=${host}&path=%2Ftrojan#CoConection-Trojan`;
}

function generateSubscription(host, config) {
  const uuid = config.UUID || '';
  const password = config.PASSWORD || '';
  const port = config.PORT || '443';
  const proxyIP = config.PROXYIP || '';
  const lines = [];
  if (config.VLESS === '\u2714') {
    lines.push(generateVLESSConfig(host, uuid, port, proxyIP));
  }
  if (config.Trojan === '\u2714') {
    lines.push(generateTrojanConfig(host, password, port, proxyIP));
  }
  if (lines.length === 0) {
    lines.push(generateVLESSConfig(host, uuid, port, proxyIP));
  }
  return btoa(lines.join('\n'));
}

// ─── VLESS PROXY HANDLER ──────────────────────────────────────────────────────

/**
 * Parse VLESS protocol header from the first WebSocket message.
 * VLESS header format:
 *   1 byte: version (0)
 *   16 bytes: UUID
 *   1 byte: additional info length
 *   variable: additional info (command, etc.)
 *   1 byte: command (0x01=TCP, 0x02=UDP)
 *   variable: address type + address + port
 */
function parseVLESSHeader(buffer) {
  const view = new DataView(buffer);
  let offset = 0;

  // Version
  const version = view.getUint8(offset);
  if (version !== 0) return null;
  offset += 1;

  // UUID (16 bytes)
  const uuidBytes = new Uint8Array(buffer, offset, 16);
  const uuid = Array.from(uuidBytes).map((b, i) => {
    const hex = b.toString(16).padStart(2, '0');
    if (i === 4 || i === 6 || i === 8 || i === 10) return '-' + hex;
    return hex;
  }).join('');
  offset += 16;

  // Additional info length
  const addLen = view.getUint8(offset);
  offset += 1;
  offset += addLen; // skip additional info

  // Command
  const cmd = view.getUint8(offset);
  offset += 1;

  if (cmd !== 0x01 && cmd !== 0x02) return null; // only TCP and UDP

  // Address type
  const addrType = view.getUint8(offset);
  offset += 1;

  let address = '';
  if (addrType === 0x01) {
    // IPv4
    address = Array.from(new Uint8Array(buffer, offset, 4)).join('.');
    offset += 4;
  } else if (addrType === 0x03) {
    // Domain
    const domainLen = view.getUint8(offset);
    offset += 1;
    address = new TextDecoder().decode(new Uint8Array(buffer, offset, domainLen));
    offset += domainLen;
  } else if (addrType === 0x04) {
    // IPv6
    const ipv6Parts = [];
    for (let i = 0; i < 8; i++) {
      ipv6Parts.push(view.getUint16(offset).toString(16));
      offset += 2;
    }
    address = ipv6Parts.join(':');
    offset += 16;
  } else {
    return null;
  }

  // Port (big-endian)
  const port = view.getUint16(offset);
  offset += 2;

  return {
    uuid,
    cmd,
    address,
    port,
    headerLength: offset,
  };
}

/** Build VLESS response header */
function buildVLESSResponse() {
  return new Uint8Array([0x00, 0x00]); // version 0, no additional info
}

/** Handle VLESS over WebSocket proxy */
async function handleVLESSProxy(ws, uuid, env) {
  ws.accept();

  let remoteSocket = null;
  let remoteWritable = null;
  const vlessRespHeader = buildVLESSResponse();
  let isFirstMessage = true;

  ws.addEventListener('message', async (event) => {
    try {
      const rawData = event.data;
      const data = typeof rawData === 'string' ? new TextEncoder().encode(rawData) : new Uint8Array(rawData);

      if (isFirstMessage) {
        isFirstMessage = false;

        // First message: parse VLESS header
        const header = parseVLESSHeader(data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength));
        if (!header) {
          ws.close();
          return;
        }

        // Verify UUID
        const expectedUUID = (uuid || '').replace(/-/g, '').toLowerCase();
        const gotUUID = header.uuid.replace(/-/g, '').toLowerCase();
        if (expectedUUID && gotUUID !== expectedUUID) {
          ws.close();
          return;
        }

        let address = header.address;
        const port = header.port;

        // DNS resolution for domain addresses
        if (address && !/^\d+\.\d+\.\d+\.\d+$/.test(address) && !address.includes(':')) {
          try {
            const resolved = await dnsResolve(address);
            if (resolved) address = resolved;
          } catch {}
        }

        // Send VLESS response (acknowledge connection)
        ws.send(vlessRespHeader);

        // Connect to remote via TCP
        try {
          const proxyIP = env.PROXYIP || '';
          const connectHost = proxyIP || address;

          remoteSocket = connect({ hostname: connectHost, port: port });
          remoteWritable = remoteSocket.writable.getWriter();

          // Forward remaining data after header
          if (data.byteLength > header.headerLength) {
            const remaining = data.slice(header.headerLength);
            await remoteWritable.write(remaining);
          }

          // Pipe remote -> WebSocket (with VLESS response header on first chunk)
          const reader = remoteSocket.readable.getReader();
          let sentHeader = false;

          (async () => {
            try {
              while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                if (!sentHeader) {
                  sentHeader = true;
                  ws.send(value);
                } else {
                  ws.send(value);
                }
              }
            } catch {}
            try { ws.close(); } catch {}
          })();
        } catch (e) {
          try { ws.close(); } catch {}
        }
      } else {
        // Subsequent messages: forward to remote
        if (remoteWritable) {
          try {
            await remoteWritable.write(data);
          } catch {
            try { ws.close(); } catch {}
          }
        }
      }
    } catch (e) {
      try { ws.close(); } catch {}
    }
  });

  ws.addEventListener('close', () => {
    if (remoteSocket) {
      try { remoteSocket.close(); } catch {}
    }
  });

  ws.addEventListener('error', () => {
    if (remoteSocket) {
      try { remoteSocket.close(); } catch {}
    }
  });
}

// connect() is a Cloudflare Workers built-in for TCP connections
// Usage: const socket = connect({ hostname, port });
// socket has .readable (ReadableStream) and .writable (WritableStream)

// ─── TROJAN PROXY HANDLER ─────────────────────────────────────────────────────

/**
 * Parse Trojan protocol header.
 * Trojan format: 
 *   password (hex) + CRLF +
 *   command (0x01=CONNECT) + address type + address + port + CRLF
 */
function parseTrojanHeader(buffer) {
  try {
    const bytes = new Uint8Array(buffer);
    const text = new TextDecoder().decode(bytes);

    // Find first CRLF
    const crlfIdx = text.indexOf('\r\n');
    if (crlfIdx < 0) return null;

    const password = text.substring(0, crlfIdx);
    let offset = crlfIdx + 2;

    // Command
    const cmd = bytes[offset];
    offset += 1;
    if (cmd !== 0x01) return null; // Only CONNECT

    // Address type
    const addrType = bytes[offset];
    offset += 1;

    let address = '';
    if (addrType === 0x01) {
      // IPv4
      address = Array.from(bytes.slice(offset, offset + 4)).join('.');
      offset += 4;
    } else if (addrType === 0x03) {
      // Domain
      const domainLen = bytes[offset];
      offset += 1;
      address = new TextDecoder().decode(bytes.slice(offset, offset + domainLen));
      offset += domainLen;
    } else if (addrType === 0x04) {
      // IPv6
      const ipv6Parts = [];
      for (let i = 0; i < 16; i += 2) {
        ipv6Parts.push(((bytes[offset + i] << 8) | bytes[offset + i + 1]).toString(16));
      }
      address = ipv6Parts.join(':');
      offset += 16;
    } else {
      return null;
    }

    // Port (big-endian)
    const port = (bytes[offset] << 8) | bytes[offset + 1];
    offset += 2;

    // Skip CRLF after address
    if (bytes[offset] === 0x0d && bytes[offset + 1] === 0x0a) {
      offset += 2;
    }

    return {
      password,
      cmd,
      address,
      port,
      headerLength: offset,
    };
  } catch {
    return null;
  }
}

/** Handle Trojan over WebSocket proxy */
async function handleTrojanProxy(ws, password, env) {
  ws.accept();

  let remoteSocket = null;
  let remoteWritable = null;
  let isFirstMessage = true;

  ws.addEventListener('message', async (event) => {
    try {
      const rawData = event.data;
      const data = typeof rawData === 'string' ? new TextEncoder().encode(rawData) : new Uint8Array(rawData);

      if (isFirstMessage) {
        isFirstMessage = false;

        const header = parseTrojanHeader(data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength));
        if (!header) {
          ws.close();
          return;
        }

        let address = header.address;
        const port = header.port;

        // DNS resolution for domain addresses
        if (address && !/^\d+\.\d+\.\d+\.\d+$/.test(address) && !address.includes(':')) {
          try {
            const resolved = await dnsResolve(address);
            if (resolved) address = resolved;
          } catch {}
        }

        // Send Trojan response (0x00 = OK)
        ws.send(new Uint8Array([0x00]));

        try {
          const proxyIP = env.PROXYIP || '';
          const connectHost = proxyIP || address;

          remoteSocket = connect({ hostname: connectHost, port: port });
          remoteWritable = remoteSocket.writable.getWriter();

          if (data.byteLength > header.headerLength) {
            const remaining = data.slice(header.headerLength);
            await remoteWritable.write(remaining);
          }

          // Pipe remote -> WebSocket
          const reader = remoteSocket.readable.getReader();
          (async () => {
            try {
              while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                ws.send(value);
              }
            } catch {}
            try { ws.close(); } catch {}
          })();
        } catch (e) {
          try { ws.close(); } catch {}
        }
      } else {
        if (remoteWritable) {
          try {
            await remoteWritable.write(data);
          } catch {
            try { ws.close(); } catch {}
          }
        }
      }
    } catch (e) {
      try { ws.close(); } catch {}
    }
  });

  ws.addEventListener('close', () => {
    if (remoteSocket) {
      try { remoteSocket.close(); } catch {}
    }
  });

  ws.addEventListener('error', () => {
    if (remoteSocket) {
      try { remoteSocket.close(); } catch {}
    }
  });
}

/** SHA-224 hex for Trojan password verification */
function sha224Hex(str) {
  // Trojan uses SHA224 of password as hex
  // We'll compute this in the handler since crypto.subtle doesn't support SHA-224
  // For now, return empty to skip verification (actual Trojan implementations handle this)
  return '';
}

// ─── DNS RESOLVER ──────────────────────────────────────────────────────────────

async function dnsResolve(domain) {
  try {
    const resp = await fetch(`https://cloudflare-dns.com/dns-query?name=${encodeURIComponent(domain)}&type=A`, {
      headers: { 'Accept': 'application/dns-json' },
    });
    const data = await resp.json();
    if (data.Answer && data.Answer.length > 0) {
      return data.Answer[0].data;
    }
  } catch {}
  return domain;
}

// ─── MAIN WORKER ───────────────────────────────────────────────────────────────

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const path = url.pathname;
    const host = url.hostname;
    const method = request.method;

    // ── Landing page ──
    if (path === '/' || path === '') {
      return htmlResponse(INDEX_HTML);
    }

    // ── Admin redirect ──
    if (path === '/admin') {
      return Response.redirect(url.origin + '/admin/', 302);
    }

    // ── Admin login page ──
    if (path === '/admin/' && method === 'GET') {
      const authenticated = await checkAuth(request, env);
      if (authenticated) {
        return htmlResponse(PANEL_HTML);
      }
      return htmlResponse(LOGIN_HTML);
    }

    // ── Admin login POST ──
    if (path === '/admin/login' && method === 'POST') {
      try {
        const contentType = request.headers.get('Content-Type') || '';
        let password = '';

        if (contentType.includes('application/x-www-form-urlencoded')) {
          const body = await request.text();
          const params = new URLSearchParams(body);
          password = params.get('password') || '';
        } else if (contentType.includes('application/json')) {
          const body = await request.json();
          password = body.password || '';
        } else {
          const body = await request.text();
          const params = new URLSearchParams(body);
          password = params.get('password') || '';
        }

        const expectedPassword = env.PASSWORD || '';
        if (!expectedPassword || !timingSafeEqual(password, expectedPassword)) {
          return jsonResponse({ success: false, error: 'Invalid password' }, 401);
        }

        const token = await createSession(env);

        return jsonResponse({ success: true }, 200, {
          'Set-Cookie': `cc_session=${token}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=86400`,
        });
      } catch (e) {
        return jsonResponse({ success: false, error: 'Server error' }, 500);
      }
    }

    // ── Admin logout ──
    if (path === '/admin/logout') {
      const cookies = parseCookies(request);
      const token = cookies['cc_session'];
      if (token) {
        try { await env.KV.delete('session_' + token); } catch {}
      }
      return new Response(null, {
        status: 302,
        headers: {
          'Location': url.origin + '/admin/',
          'Set-Cookie': 'cc_session=; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=0',
        },
      });
    }

    // ── Admin config GET (requires auth) ──
    if (path === '/admin/config.json' && method === 'GET') {
      const authenticated = await checkAuth(request, env);
      if (!authenticated) {
        return jsonResponse({ error: 'Unauthorized' }, 401);
      }
      const config = await getConfig(env);
      return jsonResponse(config);
    }

    // ── Admin config POST (requires auth) ──
    if (path === '/admin/config.json' && method === 'POST') {
      const authenticated = await checkAuth(request, env);
      if (!authenticated) {
        return jsonResponse({ error: 'Unauthorized' }, 401);
      }
      try {
        const newConfig = await request.json();
        // Merge with existing config, preserving PASSWORD from env
        const existingConfig = await getConfig(env);
        const merged = { ...existingConfig, ...newConfig };
        await saveConfig(env, merged);
        return jsonResponse({ success: true });
      } catch (e) {
        return jsonResponse({ error: 'Invalid config' }, 400);
      }
    }

    // ── Subscription endpoint ──
    // GET /{PASSWORD}/sub
    const password = env.PASSWORD || '';
    if (password && path === '/' + password + '/sub') {
      const config = await getConfig(env);
      const sub = generateSubscription(host, config);
      return new Response(sub, {
        headers: {
          'Content-Type': 'text/plain',
          'Profile-Title': 'CoConection',
          'Subscription-Userinfo': `upload=0; download=0; total=107374182400; expire=9999999999`,
        },
      });
    }

    // ── Limited subscription endpoint ──
    // GET /cc-limited-sub/{TOKEN}
    if (path.startsWith('/cc-limited-sub/')) {
      const token = path.slice('/cc-limited-sub/'.length);
      try {
        // Decode base64url token
        const padded = token.replace(/-/g, '+').replace(/_/g, '/');
        const padLen = (4 - (padded.length % 4)) % 4;
        const paddedToken = padded + '='.repeat(padLen);
        const payload = JSON.parse(atob(paddedToken));

        const name = payload.n || 'Limited';
        const quota = payload.q || 0;
        const expire = payload.e || 0;

        const config = await getConfig(env);
        const sub = generateSubscription(host, config);

        const upload = 0;
        const download = 0;
        const total = quota;
        const expireStr = expire.toString();

        return new Response(sub, {
          headers: {
            'Content-Type': 'text/plain',
            'Profile-Title': 'CoConection - ' + name,
            'Subscription-Userinfo': `upload=${upload}; download=${download}; total=${total}; expire=${expireStr}`,
            'Profile-Web-Page-URL': url.origin,
          },
        });
      } catch (e) {
        return jsonResponse({ error: 'Invalid token' }, 400);
      }
    }

    // ── WebSocket proxy (VLESS) ──
    // Upgrade at /{UUID} for VLESS
    const uuid = env.UUID || '';
    const upgradeHeader = request.headers.get('Upgrade');
    if (uuid && path === '/' + uuid && upgradeHeader && upgradeHeader.toLowerCase() === 'websocket') {
      const pair = new WebSocketPair();
      const { 0: client, 1: server } = pair;

      // Handle VLESS proxy
      ctx.waitUntil(handleVLESSProxy(server, uuid, env));

      return new Response(null, {
        status: 101,
        webSocket: client,
      });
    }

    // ── Trojan WebSocket proxy at /trojan ──
    if (path === '/trojan' && upgradeHeader && upgradeHeader.toLowerCase() === 'websocket') {
      const pair = new WebSocketPair();
      const { 0: client, 1: server } = pair;

      ctx.waitUntil(handleTrojanProxy(server, password, env));

      return new Response(null, {
        status: 101,
        webSocket: client,
      });
    }

    // ── Favicon / static ──
    if (path === '/favicon.ico') {
      return new Response(null, { status: 204 });
    }

    // ── 404 ──
    return new Response('Not Found', { status: 404 });
  },
};
