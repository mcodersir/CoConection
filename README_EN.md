<div align="center">

# CoConection

Smart connection panel with completely redesigned UI — line-style, dark/light theme, minimal inline SVG icons, and Android-first responsive layout.

<p>
  <a href="https://github.com/mcodersir">Creator: M_CODER / mcodersir</a>
  <br>
  <a href="https://github.com/IRNova/Nova-Proxy">Base Project: IRNova/Nova-Proxy</a>
</p>

---

## CoConection Changes

- Rebranded visible UI text and outputs to **CoConection**
- Completely redesigned HTML interface with clean line-style, minimal layout
- Removed external icon dependencies — replaced with inline SVG icons
- **Dark / Light theme** toggle with user preference saved to localStorage
- Android/mobile optimization: 16px inputs, 44px touch targets, safe-area, responsive grid
- Added UI layer on Worker pages without modifying the core proxy engine
- Added **Second Config** builder with custom name, data cap, and expiry
- Generates limited subscription links via:

```txt
/{PASSWORD}/cc-limited-sub/{TOKEN}
```

This link sends the following header for compatible clients:

```txt
Subscription-Userinfo: upload=0; download=0; total={BYTES}; expire={UNIX_TIME}
```

> Technical note: This feature adds volume and expiry metadata to subscription links. Actual traffic enforcement at the tunnel level depends on the core/client capabilities and infrastructure. The Nova-Proxy core is intentionally unmodified to avoid breaking connections.

---

## Files

| File | Description |
|---|---|
| `Nova System.js` | Main Worker with CoConection UI layer and limited subscription features |
| `Nova Proxy Worker V2 obfuscated.js` | Obfuscated version with the same CoConection layer |
| `Htmel/index.html` | CoConection landing page — fully local and responsive |
| `README.md` | Persian documentation |
| `README_EN.md` | English documentation (this file) |

---

## Quick Setup

### 1) Create a Worker on Cloudflare

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com/).
2. Navigate to **Workers & Pages**.
3. Click **Create Worker**.
4. Choose a name (e.g. `coconection`).
5. Copy the contents of `Nova System.js` or `Nova Proxy Worker V2 obfuscated.js` and paste into the Worker editor.
6. Click **Save and Deploy**.

### 2) Set Environment Variables

In **Settings → Variables**, configure the following:

| Variable | Required | Description |
|---|---|---|
| `PASSWORD` | ✅ Yes | Password for panel access and admin routes |
| `UUID` | ✅ Yes | UUID for VLESS — must be a valid v4 UUID |
| `KEY` | Optional | Encryption key for limited subscription signing (~32 random characters) |
| `ADMIN` | Optional | Separate admin password (falls back to `PASSWORD` if not set) |

### 3) Set up KV Namespace (if needed)

If the original Nova-Proxy uses KV:

1. In Cloudflare, go to **Workers & Pages → KV**.
2. Create a new Namespace.
3. In the Worker settings, bind the KV Namespace with the name `KV`.

### 4) Access the Panel

```txt
https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev/{PASSWORD}/
```

At the top of the panel, you'll see the **Second Config Builder** card — enter name, data cap, and days to generate a limited subscription link.

---

## Important Routes

| Route | Description |
|---|---|
| `/{PASSWORD}/` | Admin panel |
| `/{PASSWORD}/cc-limited-sub/{TOKEN}` | Limited subscription link |
| `/{PASSWORD}/__coconection/api/custom-sub` | Limited subscription creation API (POST) |

---

## Credits

- CoConection creator: [M_CODER / mcodersir](https://github.com/mcodersir)
- Base project: [IRNova/Nova-Proxy](https://github.com/IRNova/Nova-Proxy)

</div>
