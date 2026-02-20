#!/usr/bin/env python3
"""
yt-extract: fetch YouTube video metadata via the Data API v3 and print a table.
Invoke as: yt-extract [VIDEO_ID ...] or yt-extract (then prompt for IDs).
"""

import argparse
import json
import os
import re
import sys
from typing import Callable

from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from tabulate import tabulate


# --- API ---
API_BASE = "https://www.googleapis.com/youtube/v3/videos"
PARTS = "snippet,contentDetails,statistics"
BATCH_SIZE = 50


def get_api_key() -> str:
    """Read API key from environment. Exit with message if missing."""
    key = os.environ.get("YOUTUBE_DATA_API_KEY", "").strip()
    if not key:
        print("yt-extract: Set YOUTUBE_DATA_API_KEY in your environment.", file=sys.stderr)
        sys.exit(1)
    return key


def fetch_videos(api_key: str, video_ids: list[str]) -> list[dict]:
    """Fetch metadata for the given video IDs. Returns list of video resource dicts."""
    all_items: list[dict] = []
    for i in range(0, len(video_ids), BATCH_SIZE):
        chunk = video_ids[i : i + BATCH_SIZE]
        params = {
            "key": api_key,
            "part": PARTS,
            "id": ",".join(chunk),
        }
        url = f"{API_BASE}?{urlencode(params)}"
        req = Request(url)
        try:
            with urlopen(req) as resp:
                data = resp.read().decode()
        except HTTPError as e:
            body = e.read().decode() if e.fp else ""
            print(f"yt-extract: API error {e.code}: {body[:500]}", file=sys.stderr)
            sys.exit(1)
        except URLError as e:
            print(f"yt-extract: Request failed: {e.reason}", file=sys.stderr)
            sys.exit(1)
        try:
            payload = json.loads(data)
        except Exception as e:
            print(f"yt-extract: Invalid JSON response: {e}", file=sys.stderr)
            sys.exit(1)
        items = payload.get("items") or []
        all_items.extend(items)
    return all_items


# --- Duration (ISO 8601) ---
DURATION_RE = re.compile(
    r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?",
    re.IGNORECASE,
)


def parse_duration(iso_duration: str) -> str:
    """Convert ISO 8601 duration (e.g. PT55M5S) to human-readable (e.g. 55:05)."""
    if not iso_duration:
        return ""
    m = DURATION_RE.match(iso_duration.strip())
    if not m:
        return iso_duration
    h, mn, s = m.groups()
    h = int(h or 0)
    mn = int(mn or 0)
    s = int(s or 0)
    parts = []
    if h:
        parts.append(str(h))
    parts.append(f"{mn:02d}")
    parts.append(f"{s:02d}")
    return ":".join(parts)


# --- Table columns (design for future customization) ---
def _col_id(item: dict) -> str:
    return item.get("id", "")


def _col_title(item: dict) -> str:
    return (item.get("snippet") or {}).get("title", "")


def _col_publication_date(item: dict) -> str:
    raw = (item.get("snippet") or {}).get("publishedAt", "")
    if not raw:
        return ""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return raw


def _col_channel_title(item: dict) -> str:
    return (item.get("snippet") or {}).get("channelTitle", "")


def _col_view_count(item: dict) -> str:
    return (item.get("statistics") or {}).get("viewCount", "0")


def _col_like_count(item: dict) -> str:
    return (item.get("statistics") or {}).get("likeCount", "0")


def _col_comment_count(item: dict) -> str:
    return (item.get("statistics") or {}).get("commentCount", "0")


def _col_duration(item: dict) -> str:
    raw = (item.get("contentDetails") or {}).get("duration", "")
    return parse_duration(raw)


# Column id -> (header label, extractor function). Order here defines default order.
COLUMN_EXTRACTORS: dict[str, tuple[str, Callable[[dict], str]]] = {
    "id": ("id", _col_id),
    "title": ("title", _col_title),
    "publication_date": ("publication date", _col_publication_date),
    "channel_title": ("channel title", _col_channel_title),
    "view_count": ("view count", _col_view_count),
    "like_count": ("like count", _col_like_count),
    "comment_count": ("comment count", _col_comment_count),
    "duration": ("duration", _col_duration),
}

DEFAULT_TABLE_COLUMNS = [
    "id",
    "title",
    "publication_date",
    "channel_title",
    "view_count",
    "like_count",
    "comment_count",
    "duration",
]


def _escape_pipes_for_markdown(rows: list[dict]) -> list[dict]:
    """Return a copy of rows with each string cell value having '|' escaped as '\\|' for Markdown tables."""
    out = []
    for row in rows:
        out.append(
            {k: (v.replace("|", "\\|") if isinstance(v, str) else v) for k, v in row.items()}
        )
    return out


def items_to_rows(items: list[dict], columns: list[str] | None = None) -> list[dict]:
    """Build table rows from API items using the given column ids (default: DEFAULT_TABLE_COLUMNS)."""
    columns = columns or DEFAULT_TABLE_COLUMNS
    rows = []
    for item in items:
        row = {}
        for col_id in columns:
            if col_id not in COLUMN_EXTRACTORS:
                continue
            label, extractor = COLUMN_EXTRACTORS[col_id]
            row[label] = extractor(item)
        rows.append(row)
    return rows


# --- Input: normalize IDs ---
def normalize_ids(raw: list[str]) -> list[str]:
    """Split on comma/space, strip, drop empty. Optionally filter invalid format."""
    out = []
    for s in raw:
        for part in re.split(r"[\s,]+", s):
            part = part.strip()
            if not part:
                continue
            out.append(part)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch YouTube video metadata and print a table.",
    )
    parser.add_argument(
        "video_ids",
        nargs="*",
        help="One or more YouTube video IDs (or leave empty to be prompted)",
    )
    parser.add_argument(
        "--format",
        choices=["grid", "markdown"],
        default="markdown",
        help="Output table format: markdown (default) or ASCII grid",
    )
    args = parser.parse_args()
    video_ids = args.video_ids
    if not video_ids:
        try:
            prompt = "Enter video ID(s), comma- or space-separated: "
            line = input(prompt).strip()
        except EOFError:
            print("yt-extract: No video IDs provided.", file=sys.stderr)
            sys.exit(1)
        video_ids = [line] if line else []
    video_ids = normalize_ids(video_ids)
    if not video_ids:
        print("yt-extract: No video IDs provided.", file=sys.stderr)
        sys.exit(1)
    api_key = get_api_key()
    items = fetch_videos(api_key, video_ids)
    found_ids = {item.get("id") for item in items}
    for vid in video_ids:
        if vid not in found_ids:
            print(f"yt-extract: Not found: {vid}", file=sys.stderr)
    rows = items_to_rows(items)
    if not rows:
        sys.exit(1)
    tablefmt = "pipe" if args.format == "markdown" else "grid"
    if tablefmt == "pipe":
        rows = _escape_pipes_for_markdown(rows)
    print(tabulate(rows, headers="keys", tablefmt=tablefmt))


if __name__ == "__main__":
    main()
