"""Mission 1 · Task 1.1: land raw closed issues from GitHub.

Fetches closed issues (GitHub also returns PRs here; keep them, raw is untouched)
and saves them to data/raw/github/issues/<YYYY-MM-DD>.json.

Run from the project root:
    python -m ingest.github_issues

Acceptance criteria: see ARCHITECTURE.md §8 and the Task 1.1 notes.
"""

# TODO imports


OWNER = "nestjs"
REPO = "nest"
PER_PAGE = 100
MAX_PAGES = 3  # keep small while developing
RAW_DIR = None  # TODO: data/raw/github/issues (decide: relative to what?)


def get_token():
    """Read GITHUB_TOKEN from .env. Fail with a clear message if missing.
    Never print the token."""
    raise NotImplementedError  # step a


def fetch_closed_issues(token, max_pages):
    """Return a list of every item across pages.

    Follow the "next" link until there is none or max_pages is reached.
    Stop with a clear error on any non-200 response.
    Print how many items and the last X-RateLimit-Remaining.
    """
    raise NotImplementedError  # steps a, b, d


def save_raw(items, out_dir):
    """Write items as JSON to out_dir/<YYYY-MM-DD>.json and return the path.

    Must be idempotent (same day → one file) and atomic
    (a crash never leaves a half-written file at the final path).
    """
    raise NotImplementedError  # step c


def main():
    raise NotImplementedError  # wire the three functions together


if __name__ == "__main__":
    main()
