# -*- coding: utf-8 -*-
"""Integrated SenPaiScanner-style core.
The real UI calls src.core.scan_endpoints; this file exists so the scanner source is visible
inside integrated_sources without opening a separate project.
"""
from src.core import ALL_CF_WORKER_PORTS, expand_scan_endpoints, scan_endpoint, scan_endpoints, save_ip_scan_outputs

__all__ = ["ALL_CF_WORKER_PORTS", "expand_scan_endpoints", "scan_endpoint", "scan_endpoints", "save_ip_scan_outputs"]
