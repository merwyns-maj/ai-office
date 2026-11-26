"""Provider and model catalogue for the 3D office (T-056): offices/<office>/providers.yaml. Stdlib only.

Prices are USD per million tokens. They stay null until someone copies them from the provider's pricing
page and writes prices.source and prices.checked; a price without both is a problem. Never estimate one.
"""
import re
from datetime import date
from pathlib import Path

from .miniyaml import loads

FILE = "providers.yaml"
BILLINGS = ("plan", "per_token")
PRICE_KEYS = ("input", "output", "cache_read", "cache_write")
CODE_RE = re.compile(r"^[A-Z0-9]{2,4}$")
COLOUR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")
MAX_PRICE = 10000


def _price_ok(v):
    if v is None:
        return True
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= MAX_PRICE:
        return False
    return round(v, 4) == v


def _iso(v):
    if not isinstance(v, str):
        return False
    try:
        return date.fromisoformat(v).isoformat() == v
    except ValueError:
        return False


def validate(data):
    """Return a list of problem strings for a loaded catalogue (a dict of provider id -> entry)."""
    out = []
    for pid, p in data.items():
        w = f"provider {pid}"
        if not isinstance(pid, str) or not ID_RE.match(pid):
            out.append(f"{w}: bad provider id")
        if not isinstance(p, dict):
            out.append(f"{w}: must be a map")
            continue
        if p.get("billing") not in BILLINGS:
            out.append(f"{w}: billing must be plan or per_token")
        if not isinstance(p.get("code"), str) or not CODE_RE.match(p["code"]):
            out.append(f"{w}: code must be 2 to 4 capital letters or digits")
        if not isinstance(p.get("colour"), str) or not COLOUR_RE.match(p["colour"]):
            out.append(f"{w}: colour must be #rrggbb")
        models = p.get("models")
        if not isinstance(models, dict) or not models:
            out.append(f"{w}: models must be a map with at least one model")
            models = {}
        prices = p.get("prices")
        plan = p.get("billing") == "plan"
        if plan and prices is not None:
            out.append(f"{w}: a plan provider must not have prices")
        if not plan and prices is not None and not isinstance(prices, dict):
            out.append(f"{w}: prices must be a map with source and checked")
            prices = None
        priced = False
        for mid, m in models.items():
            if not isinstance(m, dict):
                out.append(f"{w}: model {mid} must be a map")
                continue
            short = m.get("short")
            if not isinstance(short, str) or not short or len(short) > 12:
                out.append(f"{w}: model {mid} needs short (1 to 12 characters)")
            for k in PRICE_KEYS:
                if k in m:
                    if plan:
                        out.append(f"{w}: plan model {mid} must not have price {k}")
                    elif not _price_ok(m[k]):
                        out.append(f"{w}: model {mid} price {k} must be null or a number from 0 to {MAX_PRICE} with at most 4 decimals")
                    elif m[k] is not None:
                        priced = True
        if priced and not plan:
            src = prices.get("source") if isinstance(prices, dict) else None
            chk = prices.get("checked") if isinstance(prices, dict) else None
            if not isinstance(src, str) or not src.strip() or not _iso(chk):
                out.append(f"{w}: a price is set but prices.source or prices.checked (YYYY-MM-DD) is missing")
    return out


def load_providers(office_root):
    """Return (catalogue dict, list of problem strings). No file gives ({}, [])."""
    path = Path(office_root) / FILE
    if not path.exists():
        return {}, []
    try:
        data = loads(path.read_text(encoding="utf-8"), str(path))
    except (OSError, ValueError) as e:
        return {}, [f"{path}: {e}"]
    data = (data or {}).get("providers") if isinstance(data, dict) else None
    if not isinstance(data, dict):
        return {}, [f"{path}: needs a top-level 'providers' map"]
    return data, [f"{path.name}: {m}" for m in validate(data)]
