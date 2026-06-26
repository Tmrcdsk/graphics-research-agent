from __future__ import annotations

import hashlib
import re


def normalize_for_hashing(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def stable_title_hash(title: str) -> str:
    return hashlib.sha256(normalize_for_hashing(title).encode("utf-8")).hexdigest()
