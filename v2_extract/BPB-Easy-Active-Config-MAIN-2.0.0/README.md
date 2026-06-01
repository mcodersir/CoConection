# BPB/Nova Easy Active Config v2

Built by **mcoders** — https://github.com/mcodersir

A transparent, local, few-click tool that deploys a Cloudflare Worker, reads a BPB-style subscription, runs Nova-inspired health checks, ranks working configs, and exports ready-to-import outputs.

## Quick start

- Windows: `run_windows.bat`
- macOS/Linux: `run_mac_linux.sh`

Main output:

```text
output/nova_best_config_only.txt
```

Backup outputs:

```text
output/nova_working_configs.txt
output/nova_quick_import.txt
output/nova_clash_meta.yaml
```

## Nova integration

The project uses a transparent Nova Easy module instead of running obfuscated code. See:

```text
src/nova_core.py
integrated_sources/Nova_Proxy_Core/
docs/NOVA_INTEGRATION_FA.md
```
