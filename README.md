# CoConection

**Simple, clean, working VPN configs in a few clicks.**

Built by **mcoders** — [github.com/mcodersir](https://github.com/mcodersir)

CoConection is a transparent, local, open-source tool that deploys a Cloudflare Worker, reads BPB-style subscriptions, runs health checks on endpoints, ranks working configs, and exports ready-to-import outputs. No CDN, no obfuscated code, no external dependencies beyond Python stdlib.

---

## Features

- **Dark/Light Theme** — Toggle with one click, preference saved in browser
- **Linear Minimal UI** — Clean design with SVG icons, no external fonts or CSS frameworks
- **3-Step Workflow** — Deploy → Test → Copy
- **Nova Easy Mode** — Automatic pre-scan, better ranking, ready-to-import output
- **Custom Config Builder** — Create additional configs with volume limits, expiry dates, custom names, protocol/port selection
- **SSE Streaming** — See test results live as each endpoint is checked
- **Auto-Save** — Settings and IP lists saved for next session
- **Multiple Export Formats** — Best config, working configs list, Clash/Mihomo YAML
- **Cross-Platform** — Windows, macOS, and Linux binaries
- **Zero External Dependencies** — Pure Python stdlib, no pip install needed

---

## Quick Start

### Option 1: Run from source

```bash
# Clone
git clone https://github.com/mcodersir/CoConection.git
cd CoConection

# Windows
run_windows.bat

# macOS/Linux
chmod +x run_mac_linux.sh
./run_mac_linux.sh
```

### Option 2: Download binary

Go to [Releases](https://github.com/mcodersir/CoConection/releases) and download the binary for your platform:

| Platform | File | Instructions |
|----------|------|-------------|
| Windows | `CoConection-Windows.exe` | Download and double-click |
| macOS | `CoConection-macOS` | Download → `chmod +x CoConection-macOS` → Run |
| Linux | `CoConection-Linux` | Download → `chmod +x CoConection-Linux` → Run |

The app starts a local HTTP server and opens your browser automatically.

---

## How to Use

### Step 1: Deploy Worker to Cloudflare

1. Sign up for a free [Cloudflare account](https://dash.cloudflare.com/sign-up)
2. Go to [API Tokens](https://dash.cloudflare.com/profile/api-tokens) and create a token with **Workers Scripts: Edit** permission
3. Enter your API Token in Step 1, click "Verify Token"
4. Enter or auto-detect your Account ID
5. Click "Generate UUID" to create a VLESS UUID
6. Click "Deploy Worker" — the app uploads the worker script to your account
7. Copy the subscription URL shown after deploy

### Step 2: Get Working Configs

1. Paste your subscription URL (or it auto-fills after deploy)
2. Select mode:
   - **Nova Easy (Recommended)** — Pre-scans IPs, tests configs, ranks by quality
   - **Smart** — Tests subscription configs directly, falls back to clean IPs
   - **Clean IP Only** — Only tests with scanned clean IPs
3. Click **Start** — watch live results stream in
4. The best config appears in Step 4

### Step 3: Custom Config Builder

1. Enter a name for your config (e.g., "Home-Device")
2. Set volume limit in GB (0 = unlimited)
3. Set expiry in days (0 = never expires)
4. Choose protocol (VLESS or Trojan), port, and network (WS or gRPC)
5. Optionally enter a clean IP to use instead of the worker domain
6. Click **Build Custom Config** — the config is generated with your settings in the name
7. Copy it or add it to the output list

### Step 4: Copy and Import

1. The best config is shown in the output textarea
2. Click **Copy Config** to copy to clipboard
3. Import in your client: Hiddify, NekoBox, v2rayN, Sing-box, etc.

---

## Output Files

All outputs are saved in the `output/` folder:

| File | Description |
|------|-------------|
| `nova_best_config_only.txt` | Single best config — import this first |
| `nova_working_configs.txt` | All working configs as backup |
| `nova_quick_import.txt` | Best + backup combined for quick import |
| `nova_clash_meta.yaml` | Clash/Mihomo proxy profile |
| `nova_bundle.json` | Full test results and metadata |
| `custom_configs.txt` | Manually built custom configs |
| `clean_ips.txt` | Clean IP scan results |
| `saved_ips.txt` | Saved IPs for reuse |

---

## Advanced Settings

| Setting | Default | Description |
|---------|---------|-------------|
| Timeout | 7s | Connection timeout per endpoint |
| Workers | 48 | Concurrent test threads |
| Limit | 2600 | Maximum configs to test |
| Random IPs | 420 | Random Cloudflare IPs to generate |
| Ports | 443, 8443, 2053, 2083 | TLS ports to test |

---

## Architecture

CoConection runs entirely locally:

- **Backend**: Python stdlib HTTP server (`start.py`) — no Flask, no Django
- **Frontend**: Single HTML + CSS + JS — no CDN, no framework
- **Worker**: BPB Worker Panel script uploaded to your Cloudflare account
- **Scanner**: Multi-phase endpoint scanner (TCP → TLS → HTTP → WebSocket DPI → Speed)
- **No data leaves your machine** — all processing is local

### Source Structure

```
CoConection/
├── start.py              # Main app (HTTP server + API)
├── cli.py                # CLI interface
├── src/
│   ├── core.py           # Config parsing, scanning, testing
│   ├── nova_core.py      # Nova Easy Mode ranking & outputs
│   └── cloudflare_deployer.py  # CF API integration
├── ui/
│   ├── index.html        # Main UI
│   ├── styles.css        # Dark/Light theme CSS
│   └── app.js            # Frontend logic
├── integrated_sources/
│   ├── BPB_Worker_Panel_Bundle/  # Worker script
│   └── Nova_Proxy_Core/         # Nova integration
├── docs/                 # Persian documentation
├── .github/workflows/    # CI/CD for binary builds
└── output/               # Generated configs (at runtime)
```

---

## Credits

- [BPB Worker Panel](https://github.com/bia-pain-bache/BPB-Worker-Panel) — Worker script
- [Nova-Proxy](https://github.com/IRNova/Nova-Proxy) — Nova Easy Mode inspiration
- [SenPaiScanner](https://github.com/MatinSenPai/SenPaiScanner) — Scanning methodology
- [v2ray-config-modifier](https://github.com/seramo/v2ray-config-modifier) — Config modification approach

---

## License

See [LICENSE](LICENSE) file.
