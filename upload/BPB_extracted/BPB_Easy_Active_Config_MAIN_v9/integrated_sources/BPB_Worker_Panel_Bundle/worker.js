// BPB Easy Internal Worker - mcoders Bundle v9
// Minimal BPB-compatible VLESS-over-WebSocket worker for deployment on the user's own Cloudflare account.
// Env vars: UUID (required), SUB_PATH (optional), PROXY_IP (optional)
import { connect } from 'cloudflare:sockets';

const FALLBACK_UUID = '__BPB_UUID__';
const FALLBACK_SUB_PATH = '__BPB_SUB_PATH__';
const FALLBACK_PROXY_IP = '__BPB_PROXY_IP__';
const encoder = new TextEncoder();
const decoder = new TextDecoder();

function uuidToBytes(uuid) {
  const clean = String(uuid || '').replace(/-/g, '').toLowerCase();
  if (!/^[0-9a-f]{32}$/.test(clean)) return null;
  const out = new Uint8Array(16);
  for (let i = 0; i < 16; i++) out[i] = parseInt(clean.slice(i * 2, i * 2 + 2), 16);
  return out;
}
function equalBytes(a, b) {
  if (!a || !b || a.length !== b.length) return false;
  let v = 0;
  for (let i = 0; i < a.length; i++) v |= a[i] ^ b[i];
  return v === 0;
}
function hostHeader(request) { return new URL(request.url).host; }
function textResponse(body, status = 200, headers = {}) {
  return new Response(body, { status, headers: { 'content-type': 'text/plain;charset=utf-8', ...headers } });
}
function htmlResponse(body) {
  return new Response(body, { headers: { 'content-type': 'text/html;charset=utf-8' } });
}
function buildVless(request, env) {
  const url = new URL(request.url);
  const host = hostHeader(request);
  const uuid = env.UUID || FALLBACK_UUID || '00000000-0000-0000-0000-000000000000';
  const name = encodeURIComponent('BPB-Easy-Cloudflare');
  const path = encodeURIComponent('/ws');
  return `vless://${uuid}@${host}:443?encryption=none&security=tls&sni=${host}&type=ws&host=${host}&path=${path}#${name}`;
}
function subPath(env) { return '/' + String(env.SUB_PATH || FALLBACK_SUB_PATH || 'sub').replace(/^\/+/, ''); }
async function handleHttp(request, env) {
  const url = new URL(request.url);
  if (url.pathname === subPath(env) || url.pathname.startsWith(subPath(env) + '/')) {
    const config = buildVless(request, env);
    const b64 = btoa(unescape(encodeURIComponent(config)));
    return textResponse(b64 + '\n');
  }
  if (url.pathname === '/raw' || url.pathname === '/config') {
    return textResponse(buildVless(request, env) + '\n');
  }
  return htmlResponse(`<!doctype html><html><head><meta charset="utf-8"><title>BPB Easy</title><style>body{font-family:Arial,sans-serif;max-width:760px;margin:40px auto;line-height:1.7;color:#111827}code,textarea{direction:ltr;display:block;width:100%;box-sizing:border-box;background:#f3f4f6;border:1px solid #d1d5db;border-radius:12px;padding:12px}a{color:#111827;font-weight:700}</style></head><body><h1>BPB Easy Internal Worker - mcoders</h1><p>Worker is running. Subscription path:</p><code>${subPath(env)}</code><p>Raw config:</p><textarea rows="6" readonly>${buildVless(request, env)}</textarea></body></html>`);
}
function readAddress(view, offset) {
  const atyp = view.getUint8(offset++);
  if (atyp === 1) {
    const parts = [];
    for (let i = 0; i < 4; i++) parts.push(view.getUint8(offset++));
    return { address: parts.join('.'), offset };
  }
  if (atyp === 2) {
    const len = view.getUint8(offset++);
    const bytes = new Uint8Array(view.buffer.slice(offset, offset + len));
    return { address: decoder.decode(bytes), offset: offset + len };
  }
  if (atyp === 3) {
    const parts = [];
    for (let i = 0; i < 8; i++) parts.push(view.getUint16(offset, false).toString(16));
    return { address: parts.join(':'), offset: offset + 16 };
  }
  throw new Error('unsupported address type');
}
function parseVlessHeader(buffer, expectedUuid) {
  if (buffer.byteLength < 24) throw new Error('invalid VLESS header');
  const bytes = new Uint8Array(buffer);
  const version = bytes[0];
  const user = bytes.slice(1, 17);
  if (!equalBytes(user, expectedUuid)) throw new Error('invalid UUID');
  let offset = 17;
  const optLen = bytes[offset++];
  offset += optLen;
  const command = bytes[offset++];
  if (command !== 1) throw new Error('only TCP command is supported');
  const view = new DataView(buffer);
  const port = view.getUint16(offset, false); offset += 2;
  const addr = readAddress(view, offset); offset = addr.offset;
  return { version, address: addr.address, port, rawData: buffer.slice(offset) };
}
async function remoteSocketToWS(remoteSocket, webSocket, vlessVersion) {
  const responseHeader = new Uint8Array([vlessVersion, 0]);
  let headerSent = false;
  const reader = remoteSocket.readable.getReader();
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      if (webSocket.readyState !== 1) break;
      if (!headerSent) {
        const chunk = new Uint8Array(value.byteLength + 2);
        chunk.set(responseHeader, 0); chunk.set(new Uint8Array(value), 2);
        webSocket.send(chunk.buffer);
        headerSent = true;
      } else {
        webSocket.send(value);
      }
    }
  } catch (_) {} finally {
    try { webSocket.close(); } catch (_) {}
  }
}
async function handleWS(request, env) {
  const expectedUuid = uuidToBytes(env.UUID || FALLBACK_UUID);
  if (!expectedUuid) return new Response('UUID env var is missing or invalid', { status: 500 });
  const pair = new WebSocketPair();
  const client = pair[0];
  const webSocket = pair[1];
  webSocket.accept();
  let remoteSocket = null;
  webSocket.addEventListener('message', async (event) => {
    try {
      const data = event.data instanceof ArrayBuffer ? event.data : await event.data.arrayBuffer();
      if (!remoteSocket) {
        const header = parseVlessHeader(data, expectedUuid);
        const targetHost = env.PROXY_IP || FALLBACK_PROXY_IP || header.address;
        remoteSocket = connect({ hostname: targetHost, port: header.port });
        const writer = remoteSocket.writable.getWriter();
        if (header.rawData && header.rawData.byteLength) await writer.write(header.rawData);
        writer.releaseLock();
        remoteSocketToWS(remoteSocket, webSocket, header.version);
      } else {
        const writer = remoteSocket.writable.getWriter();
        await writer.write(data);
        writer.releaseLock();
      }
    } catch (e) {
      try { webSocket.close(1011, String(e.message || e).slice(0, 120)); } catch (_) {}
    }
  });
  webSocket.addEventListener('close', () => { try { remoteSocket && remoteSocket.close(); } catch (_) {} });
  return new Response(null, { status: 101, webSocket: client });
}
export default {
  async fetch(request, env) {
    const upgrade = request.headers.get('Upgrade') || '';
    if (upgrade.toLowerCase() === 'websocket') return handleWS(request, env);
    return handleHttp(request, env);
  }
};
