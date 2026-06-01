# -*- coding: utf-8 -*-
"""Integrated Rasoul/v2ray-config-modifier-style core.
Endpoint replacement and bulk generation live in src.core; this module exposes them as
standalone source next to the project.
"""
from src.core import generate_modified_configs, normalize_ip_list, parse_configs, replace_endpoint, split_subscription_lines

__all__ = ["generate_modified_configs", "normalize_ip_list", "parse_configs", "replace_endpoint", "split_subscription_lines"]
