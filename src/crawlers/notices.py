"""Department notice board crawler using generic scraping."""

from __future__ import annotations

import csv
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag

from .base import BaseCrawler


# ---------------------------------------------------------------------------
# Utility helpers (adapted from TODO_dir/cnu_crawler project)

ENCODING_FALLBACKS = ["utf-8", "euc-kr", "cp949"]
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CNUNoticeBot/1.0)"
}


def resilient_get(url: str, timeout: int = 10) -> requests.Response:
    """HTTP GET with naive encoding fallback."""
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    if resp.encoding is None or "charset" not in resp.headers.get("content-type", ""):
        for enc in ENCODING_FALLBACKS:
            try:
                resp.encoding = enc
                resp.text  # trigger decode
                break
            except UnicodeDecodeError:
                continue
    resp.raise_for_status()
    return resp


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def load_links(path: Path) -> List[Tuple[str, str, str]]:
    """Load (college, dept, url) tuples from links.txt."""
    rows: List[Tuple[str, str, str]] = []
    with path.open(encoding="utf-8") as f:
        reader = csv.reader(f)
        for college, dept, url in reader:
            college = college.strip()
            dept = dept.strip()
            if college == "-":
                college = dept
            if dept == "-":
                dept = college
            rows.append((college, dept, url.strip()))
    return rows


# ---------------------------------------------------------------------------
# Generic scraper

CANDIDATE_ROWS = [
    ("table tbody tr", "td a"),
    ("div.board_list tbody tr", "td a"),
    ("ul li", "a"),
    ("div.list li", "a"),
    ("div.card", "a"),
]

_DATE_RE = re.compile(r"(20\d{2}[./-]\d{1,2}[./-]\d{1,2})|(\d{4}\.\d{2}\.\d{2})|(\d{4}-\d{2}-\d{2})")


def _extract_date(node: Tag) -> str:
    text = normalize_whitespace(node.get_text(" "))
    m = _DATE_RE.search(text)
    return m.group(0) if m else ""


def _make_id(url: str) -> str:
    return re.sub(r"\W+", "_", url) + "_" + str(int(time.time()))


def scrape_generic(college: str, dept: str, url: str) -> List[dict]:
    """Scrape a single notice list page."""
    try:
        resp = resilient_get(url, timeout=10)
    except requests.HTTPError as e:
        if e.response.status_code == 404 and "mode=list" not in url:
            fallback = url + ("?mode=list" if "?" not in url else "&mode=list")
            resp = resilient_get(fallback, timeout=10)
        else:
            raise

    base = resp.url
    soup = BeautifulSoup(resp.text, "html.parser")

    rows: List[dict] = []
    for row_sel, a_sel in CANDIDATE_ROWS:
        parsed: List[dict] = []
        for row in soup.select(row_sel):
            a_tag = row.select_one(a_sel) if a_sel else row
            if not a_tag or not a_tag.get("href"):
                continue
            title = normalize_whitespace(a_tag.get_text())
            if not title:
                continue
            href = urljoin(base, a_tag["href"].strip())
            parsed.append(
                {
                    "id": _make_id(href),
                    "title": title,
                    "url": href,
                    "posted_at": _extract_date(row),
                    "college": college,
                    "dept": dept,
                    "crawled_at": int(time.time()),
                }
            )
        if parsed:
            rows = parsed
            break

    if not rows:
        raise RuntimeError(f"No rows parsed for {url}")

    return rows


# ---------------------------------------------------------------------------
# Crawler implementation


class NoticeCrawler(BaseCrawler):
    """Crawl department notice boards listed in links.txt."""

    LINKS_FILE = Path("data/links.txt")

    def fetch(self) -> List[Tuple[str, str, str]]:
        """Load department link list.

        The original project expected ``LINKS_FILE`` to exist under
        ``TODO_dir/cnu_crawler``.  When the file is missing (for example in a
        reduced test environment) we simply return an empty list so that the
        caller can handle the absence of data gracefully rather than raising a
        ``FileNotFoundError``.
        """
        if not self.LINKS_FILE.exists():
            return []
        return load_links(self.LINKS_FILE)

    def parse(self, links: Iterable[Tuple[str, str, str]]) -> List[dict]:
        results: List[dict] = []
        for college, dept, url in links:
            try:
                rows = scrape_generic(college, dept, url)
                results.extend(rows)
            except Exception:
                # Skip failures silently
                continue
        return results

    def save(self, items: Iterable[dict]) -> None:  # type: ignore[override]
        groups: dict[Tuple[str, str], List[dict]] = {}
        for row in items:
            key = (row["college"], row["dept"])
            groups.setdefault(key, []).append(row)

        for (college, dept), rows in groups.items():
            if not rows:
                continue
            safe = lambda s: re.sub(r"[^\w가-힣]", "_", s)
            fname = f"{safe(college)}_{safe(dept)}_{datetime.now().strftime('%Y%m%d')}.csv"
            path = self.out_dir / fname
            fieldnames = ["id", "title", "url", "posted_at", "college", "dept", "crawled_at"]
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)


if __name__ == "__main__":
    crawler = NoticeCrawler(Path("data/raw/notices"))
    crawler.run()
