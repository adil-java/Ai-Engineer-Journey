"""Mission 1 · Task 1.2: read raw GitHub items and keep only real issues.

GitHub's /issues endpoint returns pull requests too; a PR is any item with a "pull_request" key.
This module never edits raw files. It only reads them.
"""

import json
from pathlib import Path

from ingest.github_issues import RAW_DIR


def latest_raw_file(raw_dir: Path = RAW_DIR) -> Path:
    files = sorted(p for p in raw_dir.glob("*.json") if not p.name.startswith("."))
    if not files:
        raise FileNotFoundError(f"No raw files in {raw_dir}. Run: python -m ingest.github_issues")
    return files[-1]  # names are YYYY-MM-DD, so lexical order == date order


def load_raw(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def is_pull_request(item: dict) -> bool:
    return "pull_request" in item


def only_issues(items: list[dict]) -> list[dict]:
    return [item for item in items if not is_pull_request(item)]


def load_issues(path: Path | None = None) -> list[dict]:
    """Issues (no PRs) from the given raw file, or from the newest one."""
    return only_issues(load_raw(path or latest_raw_file()))
