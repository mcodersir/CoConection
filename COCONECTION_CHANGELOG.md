# CoConection Changelog

## v1.0.0

### UI & Design
- Rebranded visible UI text from Nova-Proxy to **CoConection**
- Completely rebuilt HTML interface with line-style, clean and minimal design
- Added **dark/light theme** toggle with automatic system preference detection
- Preference saved to `localStorage` and persists across sessions
- Replaced all FontAwesome/Remix `<i>` icon tags with **inline local SVG icons**
- No external CDN or font dependency for icons
- Mobile-first responsive CSS: 16px inputs, 44px touch targets, safe-area padding
- Single-column layout on mobile, multi-column on desktop

### Features
- Added **Second Config Builder** on the Worker panel
  - Custom name, data cap (MB/GB), and expiry duration (days)
  - Generates a signed limited subscription link
  - Link path: `/{PASSWORD}/cc-limited-sub/{TOKEN}`
  - Sends `Subscription-Userinfo` header with volume and expiry metadata
- Added Worker response transformer that injects CoConection UI elements
  - CSS injection for line-style overrides
  - JavaScript injection for icon replacement, theme toggle, and config maker
  - Does **not** modify the Nova-Proxy core proxy engine
- Added API endpoint for creating limited subscriptions:
  - `/{PASSWORD}/__coconection/api/custom-sub` (POST)
- Added signed token system for limited subscriptions using HMAC-SHA256

### Technical Notes
- The Nova-Proxy proxy core is intentionally **unmodified** — all changes are in a separate layer
- Volume/expiry metadata in subscription headers is informational; actual traffic enforcement depends on client and infrastructure
- Works with Cloudflare Workers (requires `PASSWORD`, `UUID`, and optionally `KEY` environment variables)
- Compatible with KV namespace bindings if the base Nova-Proxy requires them

### Files
- `Nova System.js` — Full Worker with CoConection layer (readable)
- `Nova Proxy Worker V2 obfuscated.js` — Obfuscated Worker with same CoConection layer
- `Htmel/index.html` — Standalone landing page (local, no CDN)

### Credits
- CoConection creator: [M_CODER / mcodersir](https://github.com/mcodersir)
- Base project: [IRNova/Nova-Proxy](https://github.com/IRNova/Nova-Proxy)
