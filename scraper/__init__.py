"""LotClock collector.

.env is loaded here, at package import, because fetch.py and store.py read their
configuration at module level -- loading it any later would be too late.
"""
from __future__ import annotations

import os
from pathlib import Path


def _load_dotenv() -> None:
    """Load .env for local runs. No-op in CI, where the environment is already set.

    Real environment variables always win (setdefault, not assignment), so this
    can never shadow a GitHub Actions secret. Six lines beats a dependency.
    """
    path = Path(__file__).resolve().parent.parent / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()
