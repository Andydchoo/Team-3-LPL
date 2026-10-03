"""Step 5: run investigate_case on Morgan and score conflicting-evidence behavior.

Run from the repository root:

    pip install -r requirements.txt
    # ensure AWS env vars / .env are loaded
    python scripts/smoke_morgan_reliability.py

Optional:
    $env:MORGAN_RELIABILITY_RUNS = "3"
    $env:MORGAN_RELIABILITY_PAUSE = "1.25"
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from investigation.morgan import main

if __name__ == "__main__":
    raise SystemExit(main())
