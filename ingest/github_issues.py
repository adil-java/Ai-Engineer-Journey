"""Mission 1 · Task 1.1: land raw closed issues from GitHub.

Fetches closed issues from nestjs/nest and saves them, exactly as GitHub returned them,
to data/raw/github/issues/<YYYY-MM-DD>.json. GitHub's issues endpoint also returns pull
requests; they are kept here on purpose (raw is never filtered). transform/issues.py separates them.

Run from the project root:
    python -m ingest.github_issues              # MAX_PAGES pages
    python -m ingest.github_issues --pages 10

Guarantees:
- Idempotent: one file per UTC day; re-running the same day replaces it, never duplicates.
- Atomic: data goes to a temp file first, then os.replace() swaps it in, so a crash never
  leaves a half-written file at the final path.
- Fails loudly: any non-200 (after retries) stops the run and writes nothing.
"""

import argparse
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "github" / "issues"

OWNER = "nestjs"
REPO = "nest"
PER_PAGE = 100
MAX_PAGES = 3          # keep small while developing; nestjs/nest has 10k+ closed items
MAX_RETRIES = 3
MAX_WAIT_SECONDS = 60  # never sleep longer than this for one retry
TIMEOUT_SECONDS = 30

API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/issues"


class GitHubError(RuntimeError):
    pass


def get_token() -> str:
    """Read GITHUB_TOKEN from .env. Never print it."""
    load_dotenv(PROJECT_ROOT / ".env")
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise SystemExit("GITHUB_TOKEN is missing. Add it to .env (see .env.example).")
    return token


def make_session(token: str) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "whofix-ingest",
    })
    return session


def _retry_wait(response: requests.Response, attempt: int) -> float | None:
    """Seconds to wait before retrying, or None if this response should not be retried."""
    status = response.status_code
    rate_limited = status == 429 or (
        status == 403 and response.headers.get("X-RateLimit-Remaining") == "0"
    )
    if not rate_limited and status < 500:
        return None  # 401, 404, 422, plain 403 (bad permissions)... retrying won't help

    if "Retry-After" in response.headers:
        wait = float(response.headers["Retry-After"])
    elif rate_limited and "X-RateLimit-Reset" in response.headers:
        wait = float(response.headers["X-RateLimit-Reset"]) - time.time()
    else:
        wait = 2 ** attempt  # 1, 2, 4 seconds
    return max(1.0, wait)


def get_page(session: requests.Session, url: str, params: dict | None) -> requests.Response:
    """GET one page, retrying rate limits and 5xx with backoff."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = session.get(url, params=params, timeout=TIMEOUT_SECONDS)
        except (requests.ConnectionError, requests.Timeout) as exc:
            if attempt == MAX_RETRIES:
                raise GitHubError(f"Network error after {MAX_RETRIES} retries: {exc}") from exc
            time.sleep(2 ** attempt)
            continue

        if response.status_code == 200:
            return response

        wait = _retry_wait(response, attempt)
        if wait is None or attempt == MAX_RETRIES:
            raise GitHubError(
                f"GitHub returned {response.status_code} for {response.url}: {response.text[:300]}"
            )
        if wait > MAX_WAIT_SECONDS:
            raise GitHubError(f"Rate limited; reset is {wait:.0f}s away. Try again later.")
        print(f"  {response.status_code}, retrying in {wait:.0f}s (attempt {attempt + 1}/{MAX_RETRIES})")
        time.sleep(wait)

    raise AssertionError("unreachable")


def fetch_closed_issues(session: requests.Session, max_pages: int) -> list[dict]:
    """Follow the Link: rel="next" header until there are no more pages or max_pages is hit."""
    items: list[dict] = []
    url: str | None = API_URL
    params: dict | None = {"state": "closed", "per_page": PER_PAGE, "sort": "created", "direction": "desc"}
    page = 0
    remaining = "?"

    while url and page < max_pages:
        response = get_page(session, url, params)
        batch = response.json()
        if not isinstance(batch, list):
            raise GitHubError(f"Expected a JSON list, got {type(batch).__name__}")
        items.extend(batch)
        page += 1
        remaining = response.headers.get("X-RateLimit-Remaining", "?")
        print(f"  page {page}: {len(batch)} items (rate limit remaining: {remaining})")

        url = response.links.get("next", {}).get("url")
        params = None  # the "next" URL already carries the query string

    return items


def save_raw(items: list[dict], out_dir: Path, day: str) -> Path:
    """Atomically write items to out_dir/<day>.json and return the path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    final_path = out_dir / f"{day}.json"

    # Temp file in the SAME directory so os.replace() is an atomic rename on one filesystem.
    fd, tmp_name = tempfile.mkstemp(dir=out_dir, prefix=f".{day}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, final_path)
    except BaseException:  # includes KeyboardInterrupt
        Path(tmp_name).unlink(missing_ok=True)
        raise
    return final_path


def today_utc() -> str:
    # UTC, not local time: a laptop in UTC+5 and a CI runner in UTC must agree on "today".
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Land raw closed issues from GitHub.")
    parser.add_argument("--pages", type=int, default=MAX_PAGES, help=f"max pages (default {MAX_PAGES})")
    args = parser.parse_args(argv)

    session = make_session(get_token())
    print(f"Fetching closed issues from {OWNER}/{REPO} (max {args.pages} pages)...")
    try:
        items = fetch_closed_issues(session, args.pages)
    except GitHubError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    path = save_raw(items, RAW_DIR, today_utc())
    prs = sum(1 for item in items if "pull_request" in item)
    print(f"Saved {len(items)} items ({len(items) - prs} issues, {prs} PRs) to {path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
