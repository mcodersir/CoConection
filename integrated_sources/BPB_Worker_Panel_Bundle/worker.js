// BPB Easy Internal Worker v2 - mcoders Bundle
// Enhanced worker inspired by Nova-Proxy: generates VLESS + Trojan configs on multiple ports
// Env vars: UUID (required), SUB_PATH (optional, default: sub), PROXY_IP (optional)
import { connect } from 'cloudflare:sockets';

const FALLBACK_UUID = '__BPB_UUID__';
const FALLBACK_SUB_PATH = '__BPB_SUB_PATH__';
const FALLBACK_PROXY_IP = '__BPB_PROXY_IP__';
const encoder = new TextEncoder();
const decoder = new TextDecoder();

const TLS_PORTS = [443, 8443, 2053, 2083, 2087, 2096];

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

// Nova-Proxy inspired: generate multiple config types
function buildConfigs(request, env) {
  const host = hostHeader(request);
  const uuid = env.UUID || FALLBACK_UUID || '00000000-0000-0000-0000-000000000000';
  const proxyIP = env.PROXY_IP || FALLBACK_PROXY_IP || '';
  const configs = [];

  // VLESS WS TLS on all Cloudflare ports
  for (const port of TLS_PORTS) {
    const label = port === 443 ? 'BPB-VLESS-WS-TLS' : `BPB-VLESS-WS-${port}`;
    const name = encodeURIComponent(`${label}-${host.split('.')[0]}`);
    configs.push(`vless://${uuid}@${host}:${port}?encryption=none&security=tls&sni=${host}&type=ws&host=${host}&path=%2Fws#${name}`);
  }

  // VLESS gRPC TLS
  const grpcName = encodeURIComponent(`BPB-VLESS-GRPC-TLS-${host.split('.')[0]}`);
  configs.push(`vless://${uuid}@${host}:443?encryption=none&security=tls&sni=${host}&type=grpc&serviceName=grpc&host=${host}#${grpcName}`);

  // Trojan WS TLS
  const trojanHost = proxyIP || host;
  const trojanName = encodeURIComponent(`BPB-Trojan-WS-TLS-${host.split('.')[0]}`);
  configs.push(`trojan://${uuid}@${trojanHost}:443?security=tls&sni=${host}&type=ws&host=${host}&path=%2Fws#${trojanName}`);

  // Trojan on 8443
  const trojan8443Name = encodeURIComponent(`BPB-Trojan-WS-8443-${host.split('.')[0]}`);
  configs.push(`trojan://${uuid}@${trojanHost}:8443?security=tls&sni=${host}&type=ws&host=${host}&path=%2Fws#${trojan8443Name}`);

  // VLESS WS with clean IP support (if proxyIP is set)
  if (proxyIP) {
    for (const port of [443, 8443]) {
      const cleanName = encodeURIComponent(`BPB-CleanIP-VLESS-${port}-${host.split('.')[0]}`);
      configs.push(`vless://${uuid}@${proxyIP}:${port}?encryption=none&security=tls&sni=${host}&type=ws&host=${host}&path=%2Fws#${cleanName}`);
    }
  }

  return configs;
}

function subPath(env) { return '/' + String(env.SUB_PATH || FALLBACK_SUB_PATH || 'sub').replace(/^\/+/, ''); }

async function handleHttp(request, env) {
  const url = new URL(request.url);
  const sp = subPath(env);

  // Subscription endpoint (base64 encoded)
  if (url.pathname === sp || url.pathname.startsWith(sp + '/')) {
    const configs = buildConfigs(request, env);
    const b64 = btoa(unescape(encodeURIComponent(configs.join('\n'))));
    return textResponse(b64 + '\n');
  }

  // Raw config list
  if (url.pathname === '/raw' || url.pathname === '/config') {
    const configs = buildConfigs(request, env);
    return textResponse(configs.join('\n') + '\n');
  }

  // SingBox format
  if (url.pathname === '/singbox') {
    const host = hostHeader(request);
    const uuid = env.UUID || FALLBACK_UUID;
    const configs = buildConfigs(request, env);
    const outbounds = configs.filter(c => c.startsWith('vless://')).slice(0, 6).map(c => {
      const u = new URL(c);
      return {
        type: "vless", tag: decodeURIComponent(u.hash.slice(1)),
        server: u.hostname, server_port: parseInt(u.port),
        uuid: u.username, tls: { enabled: true, server_name: u.searchParams.get('sni') },
        transport: u.searchParams.get('type') === 'ws' ? { type: "ws", path: u.searchParams.get('path'), headers: { Host: u.searchParams.get('host') } } : { type: "grpc", service_name: u.searchParams.get('serviceName') || 'grpc' }
      };
    });
    return new Response(JSON.stringify({ outbounds }, null, 2), { headers: { 'content-type': 'application/json' } });
  }

  // Landing page
  const configs = buildConfigs(request, env);
  const configListHtml = configs.map(c => `<li style="margin:6px 0;padding:8px;background:#f3f4f6;border-radius:8px;word-break:break-all;direction:ltr;text-align:left;font-size:13px">${c}</li>`).join('');
  return htmlResponse(`<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BPB Easy Worker v2</title><style>body{font-family:system-ui,sans-serif;max-width:800px;margin:40px auto;padding:0 20px;line-height:1.7;color:#111827}h1{color:#0ea5e9}code{direction:ltr;display:block;background:#f3f4f6;padding:12px;border-radius:12px;overflow:auto}a{color:#0ea5e9;font-weight:700}ul{list-style:none;padding:0}</style></head><body><h1>BPB Easy Worker v2 - mcoders</h1><p>Worker is running. Total configs: <b>${configs.length}</b></p><p>Subscription path: <code>${sp}</code></p><p><a href="${sp}">Subscription Link (Base64)</a> | <a href="/raw">Raw Configs</a> | <a href="/singbox">SingBox Format</a></p><h2>All Generated Configs:</h2><ul>${configListHtml}</ul></body></html>`);
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
