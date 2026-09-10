"""Lab-rooted paths. Checklists stay in config/; cases live under data/harness/."""
from __future__ import annotations

from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = LAB_ROOT / "config"
DATA_DIR = LAB_ROOT / "data"
CASES_DIR = DATA_DIR / "harness" / "cases"
SAMPLES_DIR = DATA_DIR / "samples"
PACKS_DIR = DATA_DIR / "harness" / "packs"
FIXTURES_DIR = DATA_DIR / "harness" / "fixtures"
CHECKLISTS_DIR = CONFIG_DIR / "checklists"
POLICIES_DIR = CONFIG_DIR / "policies"
