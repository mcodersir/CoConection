/* ================= CoConection UI + Limited Subscription Layer =================
   Added by M_CODER / mcodersir. The original Nova-Proxy worker core is kept intact.
   Base project: https://github.com/IRNova/Nova-Proxy
============================================================================= */
const __COCONECTION_BRAND = 'CoConection';
const __COCONECTION_CREATOR = 'https://github.com/mcodersir';
const __COCONECTION_BASE = 'https://github.com/IRNova/Nova-Proxy';

async function __CoConectionFetch(request, env, ctx) {
  const url = new URL(request.url);
  if (url.pathname.includes('/__coconection/api/custom-sub') && request.method === 'POST') {
    return await __ccCreateCustomSub(request, env, url);
  }
  if (url.pathname.includes('/cc-limited-sub/')) {
    return await __ccServeLimitedSub(request, env, ctx, url);
  }
  const response = await __NovaOriginalWorker.fetch(request, env, ctx);
  return await __ccTransformResponse(response, request, env);
}

function __ccSafeSegment(url) {
  const parts = url.pathname.split('/').filter(Boolean);
  return parts.length ? decodeURIComponent(parts[0]) : '';
}

function __ccIsAdminPath(url, env) {
  const seg = __ccSafeSegment(url);
  const configured = String((env && (env.ADMIN || env.PASSWORD)) || '');
  if (!configured) return !!seg;
  return seg === configured;
}

function __ccJson(data, status = 200) {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=UTF-8',
      'Cache-Control': 'no-store',
      'X-CoConection': 'limited-sub'
    }
  });
}

function __ccClampNumber(value, min, max, fallback) {
  const n = Number(value);
  if (!Number.isFinite(n)) return fallback;
  return Math.min(max, Math.max(min, n));
}

function __ccBase64UrlEncode(text) {
  const bytes = new TextEncoder().encode(text);
  let binary = '';
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

function __ccBase64UrlDecode(data) {
  const b64 = data.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((data.length + 3) % 4);
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return new TextDecoder().decode(bytes);
}

async function __ccSign(input, secret) {
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign('HMAC', key, new TextEncoder().encode(input));
  let binary = '';
  for (const b of new Uint8Array(sig)) binary += String.fromCharCode(b);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

function __ccSecret(env) {
  const secret = String((env && (env.KEY || env.PASSWORD || env.ADMIN || env.UUID)) || '');
  if (!secret) throw new Error('CoConection: No signing secret configured. Set KEY, PASSWORD, ADMIN or UUID env var.');
  return secret;
}

async function __ccCreateCustomSub(request, env, url) {
  if (!__ccIsAdminPath(url, env)) return __ccJson({ success: false, message: 'Forbidden' }, 403);
  let body = {};
  try { body = await request.json(); } catch (_) {}
  const now = Math.floor(Date.now() / 1000);
  const name = String(body.name || 'CoConection Custom').replace(/[\r\n<>]/g, '').trim().slice(0, 48) || 'CoConection Custom';
  const quotaGB = __ccClampNumber(body.quotaGB, 0.1, 10240, 10);
  const days = Math.floor(__ccClampNumber(body.days, 1, 3650, 30));
  const totalBytes = Math.round(quotaGB * 1024 * 1024 * 1024);
  const payload = { n: name, q: totalBytes, e: now + days * 86400, i: now, v: 1 };
  const encoded = __ccBase64UrlEncode(JSON.stringify(payload));
  const signature = await __ccSign(encoded, __ccSecret(env));
  // Use a hash of the admin path so the password is not exposed in the subscription URL
  const adminSeg = __ccSafeSegment(url);
  const adminHash = await __ccSign(adminSeg, 'cc-path-salt');
  const subUrl = `${url.origin}/cc-limited-sub/${encoded}.${signature}`;
  return __ccJson({
    success: true,
    name,
    quotaGB: Math.round(quotaGB * 100) / 100,
    days,
    expire: payload.e,
    subscriptionUrl: subUrl,
    note: 'Limited subscription header contains total traffic and expiration metadata.'
  });
}

function __ccTimingSafeEqual(a, b) {
  if (a.length !== b.length) return false;
  let r = 0;
  for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}

async function __ccReadToken(token, env) {
  const [encoded, signature] = String(token || '').split('.');
  if (!encoded || !signature) throw new Error('bad_token');
  const expected = await __ccSign(encoded, __ccSecret(env));
  if (!__ccTimingSafeEqual(signature, expected)) throw new Error('bad_signature');
  const payload = JSON.parse(__ccBase64UrlDecode(encoded));
  if (!payload || typeof payload.q !== 'number' || !Number.isFinite(payload.q) || payload.q <= 0 ||
      typeof payload.e !== 'number' || !Number.isFinite(payload.e) || payload.e <= 0) throw new Error('bad_payload');
  return payload;
}

async function __ccServeLimitedSub(request, env, ctx, url) {
  const parts = url.pathname.split('/').filter(Boolean);
  const token = parts[parts.length - 1] || '';
  let payload;
  try { payload = await __ccReadToken(token, env); } catch (error) {
    return new Response('Invalid CoConection subscription token', { status: 403, headers: { 'Content-Type': 'text/plain; charset=UTF-8' } });
  }
  const now = Math.floor(Date.now() / 1000);
  if (payload.e < now) {
    return new Response('CoConection subscription expired', {
      status: 410,
      headers: {
        'Content-Type': 'text/plain; charset=UTF-8',
        'Subscription-Userinfo': `upload=0; download=${payload.q}; total=${payload.q}; expire=${payload.e}`,
        'X-CoConection': 'expired'
      }
    });
  }
  // Reconstruct the admin path from the original request's first segment
  const adminPath = __ccSafeSegment(url);
  const baseUrl = new URL(request.url);
  baseUrl.pathname = '/' + encodeURIComponent(adminPath) + '/';
  baseUrl.search = '';
  const upstreamReq = new Request(baseUrl.toString(), {
    method: 'GET',
    headers: {
      'Accept': 'text/plain, application/octet-stream, */*',
      'User-Agent': request.headers.get('User-Agent') || 'CoConection'
    }
  });
  const upstream = await __NovaOriginalWorker.fetch(upstreamReq, env, ctx);
  let text = await upstream.text();
  text = text
    .replace(/Nova-Proxy/g, payload.n)
    .replace(/Nova Proxy/g, payload.n)
    .replace(/IRNova/g, 'M_CODER');
  const headers = new Headers(upstream.headers);
  headers.set('Content-Type', headers.get('Content-Type') || 'text/plain; charset=UTF-8');
  headers.set('Cache-Control', 'no-store');
  headers.set('Profile-Update-Interval', '6');
  headers.set('Profile-Title', payload.n);
  headers.set('Subscription-Userinfo', `upload=0; download=0; total=${payload.q}; expire=${payload.e}`);
  headers.set('X-CoConection-Name', encodeURIComponent(payload.n));
  return new Response(text, { status: upstream.status || 200, headers });
}

async function __ccTransformResponse(response, request, env) {
  if (!response || !response.headers) return response;
  const type = response.headers.get('Content-Type') || '';
  if (!type.toLowerCase().includes('text/html')) return response;
  let html = await response.text();
  html = html
    .replace(/Nova-Proxy/g, __COCONECTION_BRAND)
    .replace(/Nova Proxy/g, __COCONECTION_BRAND)
    .replace(/IRNova\/Nova-Proxy/g, 'mcodersir/CoConection')
    .replace(/https:\/\/github\.com\/IRNova\/Nova-Proxy/g, __COCONECTION_CREATOR)
    .replace(/IRNova/g, 'M_CODER')
    .replace(/پنل پروکسی هوشمند/g, 'پنل اتصال هوشمند');
  html = html
    .replace(/<link[^>]+fonts\.googleapis\.com[^>]*>/gi, '')
    .replace(/<link[^>]+fonts\.gstatic\.com[^>]*>/gi, '')
    .replace(/<link[^>]+cdnjs\.cloudflare\.com\/ajax\/libs\/font-awesome[^>]*>/gi, '')
    .replace(/<link[^>]+remixicon[^>]*>/gi, '');
  if (!html.includes('id="cc-ui-layer"')) {
    html = html.replace('</head>', `${__ccInjectedCSS()}\n</head>`);
    html = html.replace('</body>', `${__ccInjectedScript()}\n</body>`);
  }
  const headers = new Headers(response.headers);
  headers.set('Content-Type', 'text/html; charset=UTF-8');
  headers.delete('Content-Length');
  headers.set('X-CoConection-UI', 'active');
  return new Response(html, { status: response.status, statusText: response.statusText, headers });
}

function __ccInjectedCSS() { return `<style id="cc-ui-layer">
:root{
  --cc-bg:#f8fafc;--cc-surface:#ffffff;--cc-card:#ffffff;--cc-text:#101828;--cc-muted:#667085;--cc-line:#d9e2ec;--cc-line-strong:#94a3b8;--cc-accent:#0f766e;--cc-accent-2:#2563eb;--cc-danger:#dc2626;--cc-radius:18px;--cc-shadow:none;color-scheme:light;
}
html[data-theme="dark"]{--cc-bg:#08111f;--cc-surface:#0d1728;--cc-card:#101b2d;--cc-text:#eef4ff;--cc-muted:#a9b7cc;--cc-line:#25354d;--cc-line-strong:#52647e;--cc-accent:#2dd4bf;--cc-accent-2:#60a5fa;--cc-danger:#fb7185;color-scheme:dark;}
*{font-family:Vazirmatn,Tahoma,Arial,sans-serif!important;}
body{background:var(--cc-bg)!important;color:var(--cc-text)!important;-webkit-tap-highlight-color:transparent;}
a{color:var(--cc-accent-2)!important;}
header,.header,.navbar,.topbar,.sidebar,.mobile-header{background:color-mix(in srgb,var(--cc-surface) 92%,transparent)!important;border-color:var(--cc-line)!important;box-shadow:none!important;backdrop-filter:blur(18px);}
.card,.feature-card,.stat-card,.panel,.box,.module,.config-card,.dashboard-card,.screenshot-card,.settings-card,.tab-content,.modal-content,.table-container,section{background:var(--cc-card)!important;color:var(--cc-text)!important;border:1px solid var(--cc-line)!important;box-shadow:none!important;border-radius:var(--cc-radius)!important;}
.card:hover,.feature-card:hover,.dashboard-card:hover,.config-card:hover{transform:none!important;border-color:var(--cc-line-strong)!important;}
.btn,button,input,select,textarea,.copy-btn,.action-btn,.nav-link{border-radius:14px!important;box-shadow:none!important;min-height:44px;}
.btn-primary,.primary,.active,.tab.active,button[type="submit"]{background:transparent!important;color:var(--cc-accent)!important;border:1px solid var(--cc-accent)!important;}
.btn-secondary,.secondary{background:transparent!important;color:var(--cc-text)!important;border:1px solid var(--cc-line-strong)!important;}
input,select,textarea{background:var(--cc-surface)!important;color:var(--cc-text)!important;border:1px solid var(--cc-line)!important;outline:none!important;}
input:focus,select:focus,textarea:focus{border-color:var(--cc-accent)!important;box-shadow:0 0 0 4px color-mix(in srgb,var(--cc-accent) 16%,transparent)!important;}
.logo-icon,.feature-icon,.icon,.stat-icon{background:transparent!important;color:var(--cc-accent)!important;border:1px solid var(--cc-line)!important;box-shadow:none!important;}
.logo-text,h1,h2,h3,h4{color:var(--cc-text)!important;background:none!important;-webkit-text-fill-color:currentColor!important;}
p,span,li,td,th,label,.text-muted,.muted{color:inherit;}
.badge,.tag,.chip{background:transparent!important;color:var(--cc-accent)!important;border:1px solid var(--cc-line)!important;border-radius:999px!important;}
.bg-pattern,[class*="gradient"],.blob,.glow{display:none!important;}
.cc-theme-toggle{position:fixed;left:16px;bottom:16px;z-index:99999;width:48px;height:48px;border-radius:999px;background:var(--cc-surface)!important;color:var(--cc-text)!important;border:1px solid var(--cc-line)!important;display:flex;align-items:center;justify-content:center;box-shadow:0 12px 30px rgba(0,0,0,.12)!important;}
.cc-inline-icon, .cc-theme-toggle svg{width:22px;height:22px;display:inline-flex;vertical-align:middle;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;}
.cc-config-maker{direction:rtl;margin:18px auto;padding:18px;max-width:1120px;background:var(--cc-card);border:1px solid var(--cc-line);border-radius:var(--cc-radius);color:var(--cc-text);}
.cc-config-maker *{box-sizing:border-box;}
.cc-maker-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:14px;}
.cc-maker-title{font-size:1.1rem;font-weight:800;margin:0;display:flex;gap:8px;align-items:center;}
.cc-maker-sub{margin:.3rem 0 0;color:var(--cc-muted);font-size:.92rem;line-height:1.8;}
.cc-maker-grid{display:grid;grid-template-columns:1.2fr .7fr .7fr auto;gap:10px;align-items:end;}
.cc-field label{display:block;font-size:.82rem;color:var(--cc-muted);margin-bottom:6px;}
.cc-field input{width:100%;padding:11px 12px;}
.cc-maker-btn,.cc-copy-btn{padding:10px 14px;border:1px solid var(--cc-accent)!important;background:transparent!important;color:var(--cc-accent)!important;cursor:pointer;font-weight:700;white-space:nowrap;}
.cc-output{display:none;margin-top:12px;gap:8px;grid-template-columns:1fr auto;}
.cc-output input{direction:ltr;text-align:left;font-family:ui-monospace,Menlo,Consolas,monospace!important;font-size:.84rem;}
.cc-maker-note{margin-top:10px;color:var(--cc-muted);font-size:.82rem;line-height:1.8;}
.cc-status{margin-top:10px;font-size:.88rem;color:var(--cc-muted);}
@media (max-width:900px){.cc-maker-grid{grid-template-columns:1fr 1fr}.cc-maker-btn{grid-column:1/-1}.cc-output{grid-template-columns:1fr}.cc-copy-btn{width:100%;}}
@media (max-width:768px){body{font-size:15px!important;}header,.header,.navbar{padding-inline:12px!important}.hero{min-height:auto!important;padding:92px 16px 32px!important}h1{font-size:2rem!important;line-height:1.35!important}.features,.colors-section,.screenshots-section,section{padding:42px 14px!important}.features-grid,.screenshots-grid,.grid{grid-template-columns:1fr!important;gap:12px!important}.card,.feature-card,.stat-card,.panel,.box{padding:16px!important}.btn,button{width:auto;min-width:44px}.hero-buttons{display:grid!important;grid-template-columns:1fr!important;width:100%;}.hero-buttons .btn{justify-content:center;width:100%;}.stats-section{display:grid!important;grid-template-columns:1fr 1fr!important;gap:10px!important;padding:12px!important}.cc-theme-toggle{left:12px;bottom:calc(12px + env(safe-area-inset-bottom));}.cc-config-maker{margin:12px;padding:14px}.cc-maker-grid{grid-template-columns:1fr}.cc-maker-head{display:block}}
@media (max-width:420px){h1{font-size:1.65rem!important}.stats-section{grid-template-columns:1fr!important}.cc-maker-title{font-size:1rem}.cc-config-maker{border-radius:14px}.cc-field input{font-size:16px!important}}
</style>`; }

function __ccInjectedScript() { return `<script id="cc-ui-script">
(function(){
  const brand='CoConection';
  const lineSvg={
    shield:'<svg viewBox="0 0 24 24"><path d="M12 3l7 3v5c0 5-3.2 8.5-7 10-3.8-1.5-7-5-7-10V6l7-3z"/><path d="M9 12l2 2 4-5"/></svg>',
    link:'<svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.1 0l2-2a5 5 0 0 0-7.1-7.1l-1.1 1.1"/><path d="M14 11a5 5 0 0 0-7.1 0l-2 2a5 5 0 0 0 7.1 7.1l1.1-1.1"/></svg>',
    list:'<svg viewBox="0 0 24 24"><path d="M8 6h13M8 12h13M8 18h13"/><path d="M3 6h.01M3 12h.01M3 18h.01"/></svg>',
    pulse:'<svg viewBox="0 0 24 24"><path d="M3 12h4l2-6 4 12 2-6h6"/></svg>',
    server:'<svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="6" rx="2"/><rect x="4" y="14" width="16" height="6" rx="2"/><path d="M8 7h.01M8 17h.01"/></svg>',
    globe:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.4 2.6 3.6 5.6 3.6 9s-1.2 6.4-3.6 9M12 3C9.6 5.6 8.4 8.6 8.4 12s1.2 6.4 3.6 9"/></svg>',
    code:'<svg viewBox="0 0 24 24"><path d="M8 9l-4 3 4 3M16 9l4 3-4 3M14 5l-4 14"/></svg>',
    moon:'<svg viewBox="0 0 24 24"><path d="M20 14.5A8 8 0 0 1 9.5 4 7 7 0 1 0 20 14.5z"/></svg>',
    sun:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>',
    plus:'<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>'
  };
  function iconFor(cls){cls=String(cls||''); if(/github|code|robot|terminal/.test(cls))return'code'; if(/link|chain|copy/.test(cls))return'link'; if(/list|menu|config|tachometer/.test(cls))return'list'; if(/heart|ping|activity/.test(cls))return'pulse'; if(/server|cloud|database/.test(cls))return'server'; if(/globe|network|telegram/.test(cls))return'globe'; return'shield';}
  function replaceIcons(){document.querySelectorAll('i[class]:not([data-cc-done])').forEach(function(i){const span=document.createElement('span');span.className='cc-inline-icon';span.innerHTML=lineSvg[iconFor(i.className)]||lineSvg.shield;i.replaceWith(span);});}
  function setTheme(mode){document.documentElement.setAttribute('data-theme',mode);try{localStorage.setItem('cc-theme',mode)}catch(e){} const btn=document.querySelector('.cc-theme-toggle'); if(btn)btn.innerHTML=lineSvg[mode==='dark'?'sun':'moon'];}
  function initTheme(){let saved='';try{saved=localStorage.getItem('cc-theme')||''}catch(e){} setTheme(saved || (matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light')); const btn=document.createElement('button');btn.className='cc-theme-toggle';btn.type='button';btn.setAttribute('aria-label','تغییر تم');btn.onclick=function(){setTheme(document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark')};document.body.appendChild(btn);setTheme(document.documentElement.getAttribute('data-theme')||'light');}
  function findMount(){return document.querySelector('main')||document.querySelector('.main-content')||document.querySelector('.dashboard')||document.querySelector('.content')||document.querySelector('.container')||document.body;}
  function addMaker(){if(document.querySelector('.cc-config-maker'))return; const seg=location.pathname.split('/').filter(Boolean)[0]; if(!seg)return; const card=document.createElement('section');card.className='cc-config-maker';card.innerHTML='<div class="cc-maker-head"><div><h3 class="cc-maker-title"><span class="cc-inline-icon">'+lineSvg.plus+'</span> ساخت کانفیگ دوم</h3><p class="cc-maker-sub">یک لینک اشتراک اختصاصی بساز؛ حجم و زمان آن در هدر اشتراک برای کلاینت‌ها نمایش داده می‌شود.</p></div></div><form class="cc-maker-grid"><div class="cc-field"><label>نام کانفیگ</label><input name="name" value="CoConection Custom" maxlength="48"></div><div class="cc-field"><label>حجم / گیگابایت</label><input name="quotaGB" type="number" min="0.1" step="0.1" value="30"></div><div class="cc-field"><label>مدت / روز</label><input name="days" type="number" min="1" step="1" value="30"></div><button class="cc-maker-btn" type="submit">ساخت لینک</button></form><div class="cc-output"><input readonly><button class="cc-copy-btn" type="button">کپی</button></div><div class="cc-status"></div><p class="cc-maker-note">کانفیگ اول همان لینک اصلی خود پنل است؛ این بخش یک لینک دوم با متادیتای حجم و انقضا می‌سازد.</p>'; const mount=findMount(); if(mount===document.body)document.body.insertBefore(card,document.body.firstChild);else mount.prepend(card); const form=card.querySelector('form'),status=card.querySelector('.cc-status'),out=card.querySelector('.cc-output'),input=out.querySelector('input'),copy=out.querySelector('button'); form.addEventListener('submit',async function(e){e.preventDefault();status.textContent='در حال ساخت...';out.style.display='none';const data=Object.fromEntries(new FormData(form).entries());try{const res=await fetch('/'+encodeURIComponent(seg)+'/__coconection/api/custom-sub',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const json=await res.json();if(!json.success)throw new Error(json.message||'خطا');input.value=json.subscriptionUrl;out.style.display='grid';status.textContent='آماده شد؛ لینک را در کلاینت وارد کن.';}catch(err){status.textContent='ساخت لینک انجام نشد: '+(err&&err.message?err.message:'خطای ناشناخته');}}); copy.onclick=async function(){try{await navigator.clipboard.writeText(input.value);status.textContent='کپی شد.';}catch(e){input.select();document.execCommand('copy');status.textContent='کپی شد.';}};}
  document.title=document.title.replace(/Nova-Proxy|Nova Proxy/g,brand);
  document.addEventListener('DOMContentLoaded',function(){replaceIcons();initTheme();addMaker();});
})();
</script>`; }

export default { async fetch(request, env, ctx) { return await __CoConectionFetch(request, env, ctx); } };
