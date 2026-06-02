'use strict';

/**
 * Koyra One v1.0.0
 * One-file personal VLESS-over-WebSocket endpoint for Node.js/Koyeb.
 * Transparent, dependency-free, no obfuscation.
 *
 * Personal-use note: run only for your own lawful/private traffic and respect your provider rules.
 */

const http = require('http');
const net = require('net');
const crypto = require('crypto');
const { URL } = require('url');

const APP_NAME = 'Koyra One';
const VERSION = '1.0.0';
const PORT = parseInt(process.env.PORT || '3000', 10);
const WS_PATH = normalizePath(process.env.KOYRA_PATH || '/koyra');
const REMARK = process.env.KOYRA_REMARK || 'Koyra-One';
const SUB_TOKEN = (process.env.KOYRA_SUB_TOKEN || '').trim();
const ADMIN_KEY = (process.env.KOYRA_ADMIN_KEY || '').trim();
const PREFERRED_HOST = (process.env.KOYRA_PUBLIC_HOST || '').trim();
const KEY_SEED = (process.env.KOYRA_KEY || '').trim();
const UUID = normalizeUuid(process.env.KOYRA_UUID || (KEY_SEED ? uuidFromSeed(KEY_SEED) : uuidFromSeed('CHANGE-ME-KOYRA-ONE')));
const INSECURE_DEFAULT = !process.env.KOYRA_UUID && !KEY_SEED;

function normalizePath(p) {
  p = String(p || '/koyra').trim();
  if (!p.startsWith('/')) p = '/' + p;
  return p.replace(/\/+/g, '/');
}

function normalizeUuid(u) {
  u = String(u || '').trim().toLowerCase();
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(u)) {
    return uuidFromSeed(u || 'CHANGE-ME-KOYRA-ONE');
  }
  return u;
}

function uuidFromSeed(seed) {
  const h = crypto.createHash('sha256').update(String(seed)).digest();
  h[6] = (h[6] & 0x0f) | 0x40; // UUID v4-style version bits
  h[8] = (h[8] & 0x3f) | 0x80; // variant bits
  const hex = h.subarray(0, 16).toString('hex');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20, 32)}`;
}

function uuidToBytes(uuid) {
  return Buffer.from(uuid.replace(/-/g, ''), 'hex');
}

const UUID_BYTES = uuidToBytes(UUID);

function htmlEscape(s) {
  return String(s).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}

function publicHost(req) {
  return PREFERRED_HOST || req.headers['x-forwarded-host'] || req.headers.host || `localhost:${PORT}`;
}

function proto(req) {
  return (req.headers['x-forwarded-proto'] || 'https').split(',')[0].trim() || 'https';
}

function subPath() {
  return SUB_TOKEN ? `/sub/${encodeURIComponent(SUB_TOKEN)}` : '/sub';
}

function hasSubAccess(req, pathname) {
  if (!SUB_TOKEN) return true;
  if (pathname === `/sub/${SUB_TOKEN}` || pathname === `/config/${SUB_TOKEN}` || pathname === `/json/${SUB_TOKEN}`) return true;
  const u = new URL(req.url, 'http://local');
  return u.searchParams.get('token') === SUB_TOKEN;
}

function hasAdminAccess(req) {
  if (!ADMIN_KEY) return true;
  const u = new URL(req.url, 'http://local');
  return u.searchParams.get('key') === ADMIN_KEY || req.headers['x-koyra-admin-key'] === ADMIN_KEY;
}

function makeVlessLink(req) {
  const host = publicHost(req).replace(/:\d+$/, '');
  const encodedPath = encodeURIComponent(WS_PATH);
  const name = encodeURIComponent(REMARK);
  return `vless://${UUID}@${host}:443?encryption=none&security=tls&sni=${host}&fp=chrome&type=ws&host=${host}&path=${encodedPath}#${name}`;
}

function makeSubscription(req) {
  const txt = makeVlessLink(req) + '\n';
  return Buffer.from(txt, 'utf8').toString('base64');
}

function makeSingBoxJson(req) {
  const host = publicHost(req).replace(/:\d+$/, '');
  return {
    outbounds: [
      {
        type: 'vless',
        tag: REMARK,
        server: host,
        server_port: 443,
        uuid: UUID,
        tls: {
          enabled: true,
          server_name: host,
          utls: { enabled: true, fingerprint: 'chrome' }
        },
        transport: {
          type: 'ws',
          path: WS_PATH,
          headers: { Host: host }
        },
        packet_encoding: ''
      }
    ]
  };
}

function send(res, status, body, type = 'text/plain; charset=utf-8') {
  const buf = Buffer.isBuffer(body) ? body : Buffer.from(String(body), 'utf8');
  res.writeHead(status, {
    'content-type': type,
    'content-length': buf.length,
    'cache-control': 'no-store'
  });
  res.end(buf);
}

function page(req) {
  const host = publicHost(req);
  const base = `${proto(req)}://${host}`;
  const vless = makeVlessLink(req);
  const sub = `${base}${subPath()}`;
  const warning = INSECURE_DEFAULT
    ? `<div class="warn">هشدار: KOYRA_KEY یا KOYRA_UUID تنظیم نشده. برای استفاده واقعی، در Koyeb یک KOYRA_KEY اختصاصی بگذار.</div>`
    : '';
  return `<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>${APP_NAME}</title>
<style>
:root{--bg:#0b0f14;--card:#101821;--line:#203040;--text:#eef5ff;--muted:#91a4b8;--ok:#43d189;--warn:#f7bd4b;--bad:#ff6b6b;--accent:#6aa9ff}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top,#132034,#0b0f14 55%);color:var(--text);font-family:Tahoma,Arial,sans-serif;line-height:1.8}.wrap{max-width:980px;margin:0 auto;padding:28px 14px}.hero{border:1px solid var(--line);border-radius:24px;padding:24px;background:linear-gradient(180deg,rgba(255,255,255,.045),rgba(255,255,255,.015));box-shadow:0 18px 50px rgba(0,0,0,.25)}h1{margin:0 0 8px;font-size:32px}.pill{display:inline-flex;gap:8px;align-items:center;border:1px solid var(--line);border-radius:99px;padding:6px 12px;color:var(--muted);font-size:13px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:16px}.card{border:1px solid var(--line);border-radius:18px;padding:16px;background:rgba(16,24,33,.82)}.label{color:var(--muted);font-size:13px;margin-bottom:6px}.value{direction:ltr;text-align:left;word-break:break-all;background:#081018;border:1px solid #1b2a39;border-radius:14px;padding:12px;font-family:ui-monospace,Consolas,monospace;font-size:13px}.btns{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}.btn{border:1px solid var(--line);border-radius:14px;padding:10px 14px;color:var(--text);text-decoration:none;background:#111b26}.btn:hover{border-color:var(--accent)}.ok{color:var(--ok)}.warn{margin-top:14px;border:1px solid rgba(247,189,75,.45);background:rgba(247,189,75,.09);border-radius:16px;padding:12px;color:#ffe0a1}.footer{margin-top:22px;color:var(--muted);font-size:13px}@media(max-width:760px){.grid{grid-template-columns:1fr}h1{font-size:26px}.wrap{padding:18px 10px}}
</style>
</head>
<body><main class="wrap"><section class="hero">
<div class="pill">● ${APP_NAME} v${VERSION}</div>
<h1>کانفیگ شخصی VLESS روی Koyeb</h1>
<p>این سرویس یک endpoint شخصی VLESS-over-WebSocket می‌دهد. لینک Subscription را در v2rayN / NekoBox / Hiddify / Sing-box وارد کن.</p>
${warning}
<div class="grid">
<div class="card"><div class="label">وضعیت</div><div class="value ok">OK — WebSocket path: ${htmlEscape(WS_PATH)}</div></div>
<div class="card"><div class="label">Subscription</div><div class="value">${htmlEscape(sub)}</div></div>
<div class="card"><div class="label">VLESS URI</div><div class="value">${htmlEscape(vless)}</div></div>
<div class="card"><div class="label">UUID</div><div class="value">${htmlEscape(UUID)}</div></div>
</div>
<div class="btns">
<a class="btn" href="${htmlEscape(sub)}">دانلود Subscription</a>
<a class="btn" href="/config${SUB_TOKEN ? '/' + encodeURIComponent(SUB_TOKEN) : ''}">نمایش کانفیگ خام</a>
<a class="btn" href="/json${SUB_TOKEN ? '/' + encodeURIComponent(SUB_TOKEN) : ''}">Sing-box JSON</a>
<a class="btn" href="/health">Health</a>
</div>
<div class="footer">Koyra One — transparent single-file JS runtime.</div>
</section></main></body></html>`;
}

function handleHttp(req, res) {
  const u = new URL(req.url, 'http://local');
  const pathname = u.pathname.replace(/\/+$/, '') || '/';
  if (pathname === '/') return send(res, 200, page(req), 'text/html; charset=utf-8');
  if (pathname === '/health') {
    return send(res, 200, JSON.stringify({ ok: true, app: APP_NAME, version: VERSION, ws_path: WS_PATH, insecure_default: INSECURE_DEFAULT }, null, 2), 'application/json; charset=utf-8');
  }
  if (pathname === '/debug') {
    if (!hasAdminAccess(req)) return send(res, 403, 'forbidden');
    return send(res, 200, JSON.stringify({ app: APP_NAME, version: VERSION, port: PORT, host: publicHost(req), uuid: UUID, path: WS_PATH, sub_path: subPath(), insecure_default: INSECURE_DEFAULT }, null, 2), 'application/json; charset=utf-8');
  }
  if (pathname === '/sub' || pathname.startsWith('/sub/')) {
    if (!hasSubAccess(req, pathname)) return send(res, 403, 'forbidden');
    return send(res, 200, makeSubscription(req), 'text/plain; charset=utf-8');
  }
  if (pathname === '/config' || pathname.startsWith('/config/')) {
    if (!hasSubAccess(req, pathname)) return send(res, 403, 'forbidden');
    return send(res, 200, makeVlessLink(req) + '\n', 'text/plain; charset=utf-8');
  }
  if (pathname === '/json' || pathname.startsWith('/json/')) {
    if (!hasSubAccess(req, pathname)) return send(res, 200, 'forbidden');
    return send(res, 200, JSON.stringify(makeSingBoxJson(req), null, 2), 'application/json; charset=utf-8');
  }
  send(res, 404, 'not found');
}

function acceptWebSocket(req, socket) {
  const key = req.headers['sec-websocket-key'];
  if (!key) return socket.destroy();
  const accept = crypto.createHash('sha1').update(key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest('base64');
  socket.write([
    'HTTP/1.1 101 Switching Protocols',
    'Upgrade: websocket',
    'Connection: Upgrade',
    `Sec-WebSocket-Accept: ${accept}`,
    '', ''
  ].join('\r\n'));
  return true;
}

class WsFrameParser {
  constructor(onFrame) {
    this.buf = Buffer.alloc(0);
    this.onFrame = onFrame;
  }
  push(chunk) {
    this.buf = Buffer.concat([this.buf, chunk]);
    while (this.buf.length >= 2) {
      const b0 = this.buf[0], b1 = this.buf[1];
      const opcode = b0 & 0x0f;
      const masked = !!(b1 & 0x80);
      let len = b1 & 0x7f;
      let off = 2;
      if (len === 126) {
        if (this.buf.length < off + 2) return;
        len = this.buf.readUInt16BE(off); off += 2;
      } else if (len === 127) {
        if (this.buf.length < off + 8) return;
        const hi = this.buf.readUInt32BE(off); const lo = this.buf.readUInt32BE(off + 4); off += 8;
        if (hi !== 0) throw new Error('WebSocket frame too large');
        len = lo;
      }
      let mask;
      if (masked) {
        if (this.buf.length < off + 4) return;
        mask = this.buf.subarray(off, off + 4); off += 4;
      }
      if (this.buf.length < off + len) return;
      let payload = Buffer.from(this.buf.subarray(off, off + len));
      this.buf = this.buf.subarray(off + len);
      if (masked) {
        for (let i = 0; i < payload.length; i++) payload[i] ^= mask[i & 3];
      }
      this.onFrame(opcode, payload);
    }
  }
}

function wsFrame(payload, opcode = 2) {
  if (!Buffer.isBuffer(payload)) payload = Buffer.from(payload || '');
  const len = payload.length;
  let header;
  if (len < 126) {
    header = Buffer.from([0x80 | opcode, len]);
  } else if (len < 65536) {
    header = Buffer.alloc(4);
    header[0] = 0x80 | opcode; header[1] = 126; header.writeUInt16BE(len, 2);
  } else {
    header = Buffer.alloc(10);
    header[0] = 0x80 | opcode; header[1] = 127; header.writeUInt32BE(0, 2); header.writeUInt32BE(len, 6);
  }
  return Buffer.concat([header, payload]);
}

function parseVlessHeader(buf) {
  if (buf.length < 24) throw new Error('short VLESS header');
  let off = 0;
  const version = buf[off++];
  const id = buf.subarray(off, off + 16); off += 16;
  if (!id.equals(UUID_BYTES)) throw new Error('invalid UUID');
  const optLen = buf[off++];
  off += optLen;
  if (buf.length < off + 4) throw new Error('short VLESS command');
  const command = buf[off++];
  const port = buf.readUInt16BE(off); off += 2;
  const addrType = buf[off++];
  let address;
  if (addrType === 1) {
    if (buf.length < off + 4) throw new Error('short IPv4');
    address = Array.from(buf.subarray(off, off + 4)).join('.'); off += 4;
  } else if (addrType === 2) {
    const l = buf[off++];
    if (buf.length < off + l) throw new Error('short domain');
    address = buf.subarray(off, off + l).toString('utf8'); off += l;
  } else if (addrType === 3) {
    if (buf.length < off + 16) throw new Error('short IPv6');
    const parts = [];
    for (let i = 0; i < 8; i++) parts.push(buf.readUInt16BE(off + i * 2).toString(16));
    address = parts.join(':'); off += 16;
  } else {
    throw new Error('unsupported address type');
  }
  return { version, command, port, address, data: buf.subarray(off) };
}

function handleVlessWs(req, socket) {
  if (!acceptWebSocket(req, socket)) return;
  let remote = null;
  let established = false;
  let closed = false;

  function closeAll() {
    if (closed) return;
    closed = true;
    try { if (remote) remote.destroy(); } catch (_) {}
    try { socket.end(wsFrame(Buffer.alloc(0), 8)); } catch (_) { try { socket.destroy(); } catch (__) {} }
  }

  const parser = new WsFrameParser((opcode, payload) => {
    try {
      if (opcode === 8) return closeAll();
      if (opcode === 9) return socket.write(wsFrame(payload, 10));
      if (opcode !== 2 && opcode !== 1) return;

      if (!established) {
        const reqInfo = parseVlessHeader(payload);
        if (reqInfo.command !== 1) throw new Error('only TCP command is supported in v1');
        established = true;
        remote = net.createConnection({ host: reqInfo.address, port: reqInfo.port }, () => {
          socket.write(wsFrame(Buffer.from([reqInfo.version, 0]), 2));
          if (reqInfo.data.length) remote.write(reqInfo.data);
        });
        remote.on('data', chunk => { if (!closed) socket.write(wsFrame(chunk, 2)); });
        remote.on('error', () => closeAll());
        remote.on('end', () => closeAll());
        remote.on('close', () => closeAll());
      } else if (remote && !remote.destroyed) {
        remote.write(payload);
      }
    } catch (e) {
      closeAll();
    }
  });

  socket.on('data', chunk => {
    try { parser.push(chunk); } catch (_) { closeAll(); }
  });
  socket.on('error', () => closeAll());
  socket.on('end', () => closeAll());
  socket.on('close', () => closeAll());
}

const server = http.createServer(handleHttp);
server.on('upgrade', (req, socket) => {
  const u = new URL(req.url, 'http://local');
  if (u.pathname !== WS_PATH) return socket.destroy();
  handleVlessWs(req, socket);
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`${APP_NAME} v${VERSION} listening on :${PORT}`);
  console.log(`WS path: ${WS_PATH}`);
  console.log(`UUID: ${UUID}${INSECURE_DEFAULT ? '  (set KOYRA_KEY or KOYRA_UUID)' : ''}`);
});
