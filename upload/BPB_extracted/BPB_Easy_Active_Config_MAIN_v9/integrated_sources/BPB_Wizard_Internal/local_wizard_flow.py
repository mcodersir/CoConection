# -*- coding: utf-8 -*-
"""Internal wizard flow used by the v9 UI.
This file documents the integrated BPB Wizard logic: collect Cloudflare token/account,
prepare a worker bundle, deploy it, then guide the user to copy the Subscription URL.
"""
from dataclasses import dataclass

@dataclass
class WizardState:
    email_ready: bool = False
    cloudflare_ready: bool = False
    api_token_checked: bool = False
    worker_deployed: bool = False
    subscription_url: str = ""

STEPS_FA = [
    "ایمیل قابل‌دسترسی پروژه/Atomic Mail را آماده کن.",
    "حساب Cloudflare را بساز یا وارد Dashboard شو.",
    "API Token و Account ID را وارد کن.",
    "Worker داخلی BPB را Deploy کن.",
    "پنل/دامنه Worker را باز کن و Subscription را بگیر.",
    "Subscription را به اسکنر و Config Modifier داخلی بده.",
]
