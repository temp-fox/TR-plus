# coding=utf-8
"""
Export TrendRadar SQLite output to repository-friendly JSON files.

This script is intentionally independent from the trendradar package internals so
forks can keep the upstream code mostly unchanged. It reads local SQLite files
created under output/news and output/rss, then writes compact JSON snapshots to
output/json for other repositories to consume.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from trendradar.core.frequency import _word_matches, load_frequency_words  # noqa: E402

OUTPUT_DIR = ROOT / "output"
NEWS_DIR = OUTPUT_DIR / "news"
RSS_DIR = OUTPUT_DIR / "rss"
JSON_DIR = OUTPUT_DIR / "json"
RETENTION_DAYS = 7
DATE_FORMAT = "%Y-%m-%d"


def _now_beijing() -> datetime:
    return datetime.now(timezone(timedelta(hours=8)))


def _latest_db(db_dir: Path) -> Optional[Path]:
    if not db_dir.exists():
        return None
    db_files = sorted(db_dir.glob("*.db"), key=lambda p: p.name)
    return db_files[-1] if db_files else None


def _fetch_all(conn: sqlite3.Connection, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def _match_category(
    title: str,
    word_groups: List[Dict[str, Any]],
    filter_words: List[Any],
    global_filters: List[str],
) -> Optional[str]:
    """Return the first configured category matched by title, or None."""
    if not isinstance(title, str) or not title.strip():
        return None

    title_lower = title.lower()
    if any(global_word.lower() in title_lower for global_word in global_filters):
        return None
    if any(_word_matches(filter_word, title_lower) for filter_word in filter_words):
        return None

    for group in word_groups:
        required_words = group.get("required", [])
        normal_words = group.get("normal", [])

        if required_words and not all(_word_matches(word, title_lower) for word in required_words):
            continue
        if normal_words and not any(_word_matches(word, title_lower) for word in normal_words):
            continue

        return group.get("display_name") or group.get("group_key") or "未分类"

    return None


def _item_ref(source_type: str, item: Dict[str, Any]) -> str:
    return f"{source_type}:{item.get('id')}"


def _category_refs(items: List[Dict[str, Any]], source_type: str) -> Dict[str, List[str]]:
    categories: Dict[str, List[str]] = {}
    for item in items:
        category = item.get("matched_category")
        if not category:
            continue
        categories.setdefault(category, []).append(_item_ref(source_type, item))
    return categories


def _filter_and_group_items(
    items: List[Dict[str, Any]],
    word_groups: List[Dict[str, Any]],
    filter_words: List[Any],
    global_filters: List[str],
) -> List[Dict[str, Any]]:
    filtered: List[Dict[str, Any]] = []

    for item in items:
        category = _match_category(item.get("title", ""), word_groups, filter_words, global_filters)
        if not category:
            continue
        enriched = dict(item)
        enriched["matched_category"] = category
        enriched["item_id"] = _item_ref("news" if "platform_id" in enriched else "rss", enriched)
        filtered.append(enriched)

    return filtered


def _apply_keyword_filter(
    news: Dict[str, Any],
    rss: Dict[str, Any],
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    word_groups, filter_words, global_filters = load_frequency_words("config/frequency_words.txt")

    news_items = _filter_and_group_items(news.get("items", []), word_groups, filter_words, global_filters)
    rss_items = _filter_and_group_items(rss.get("items", []), word_groups, filter_words, global_filters)

    news_latest_ids = [
        _item_ref("news", item)
        for item in news_items
        if item.get("is_latest")
    ]
    rss_latest_ids = [
        _item_ref("rss", item)
        for item in rss_items
        if item.get("is_latest")
    ]

    news_categories = _category_refs(news_items, "news")
    rss_categories = _category_refs(rss_items, "rss")
    latest_news_categories = _category_refs(
        [item for item in news_items if item.get("is_latest")],
        "news",
    )
    latest_rss_categories = _category_refs(
        [item for item in rss_items if item.get("is_latest")],
        "rss",
    )

    filtered_news = dict(news)
    filtered_news["items"] = news_items
    filtered_news["latest_item_ids"] = news_latest_ids
    filtered_news.pop("latest_items", None)
    filtered_news["categories"] = news_categories
    filtered_news["latest_categories"] = latest_news_categories
    filtered_news["raw_count"] = news.get("count", 0)
    filtered_news["raw_latest_count"] = news.get("latest_count", 0)
    filtered_news["count"] = len(news_items)
    filtered_news["latest_count"] = len(news_latest_ids)

    filtered_rss = dict(rss)
    filtered_rss["items"] = rss_items
    filtered_rss["latest_item_ids"] = rss_latest_ids
    filtered_rss.pop("latest_items", None)
    filtered_rss["categories"] = rss_categories
    filtered_rss["latest_categories"] = latest_rss_categories
    filtered_rss["raw_count"] = rss.get("count", 0)
    filtered_rss["raw_latest_count"] = rss.get("latest_count", 0)
    filtered_rss["count"] = len(rss_items)
    filtered_rss["latest_count"] = len(rss_latest_ids)

    combined_categories: Dict[str, Dict[str, List[str]]] = {}
    for category, ids in news_categories.items():
        combined_categories.setdefault(category, {"news": [], "rss": []})["news"] = ids
    for category, ids in rss_categories.items():
        combined_categories.setdefault(category, {"news": [], "rss": []})["rss"] = ids

    return filtered_news, filtered_rss, combined_categories


def _read_news(db_path: Optional[Path]) -> Dict[str, Any]:
    if not db_path or not db_path.exists():
        return {"date": None, "latest_crawl_time": None, "items": [], "platforms": []}

    date = db_path.stem
    with sqlite3.connect(db_path) as conn:
        latest_row = conn.execute(
            "SELECT crawl_time FROM crawl_records ORDER BY crawl_time DESC LIMIT 1"
        ).fetchone()
        latest_crawl_time = latest_row[0] if latest_row else None

        platforms = _fetch_all(
            conn,
            """
            SELECT id, name, is_active, updated_at
            FROM platforms
            ORDER BY id
            """,
        )

        items = _fetch_all(
            conn,
            """
            SELECT
                n.id,
                n.title,
                n.platform_id,
                COALESCE(p.name, n.platform_id) AS platform_name,
                n.rank,
                n.url,
                n.mobile_url,
                n.first_crawl_time,
                n.last_crawl_time,
                n.crawl_count,
                n.created_at,
                n.updated_at,
                (
                    SELECT json_group_array(rank)
                    FROM (
                        SELECT rh.rank AS rank
                        FROM rank_history rh
                        WHERE rh.news_item_id = n.id
                        ORDER BY rh.crawl_time ASC, rh.id ASC
                    )
                ) AS ranks,
                (
                    SELECT json_group_array(json_object('rank', rank, 'crawl_time', crawl_time))
                    FROM (
                        SELECT rh.rank AS rank, rh.crawl_time AS crawl_time
                        FROM rank_history rh
                        WHERE rh.news_item_id = n.id
                        ORDER BY rh.crawl_time ASC, rh.id ASC
                    )
                ) AS rank_timeline
            FROM news_items n
            LEFT JOIN platforms p ON p.id = n.platform_id
            ORDER BY n.last_crawl_time DESC, n.platform_id ASC, n.rank ASC, n.id ASC
            """,
        )

    for item in items:
        item["ranks"] = json.loads(item["ranks"] or "[]")
        item["rank_timeline"] = json.loads(item["rank_timeline"] or "[]")
        item["is_latest"] = bool(latest_crawl_time and item.get("last_crawl_time") == latest_crawl_time)

    latest_items = [item for item in items if item["is_latest"]]
    return {
        "date": date,
        "latest_crawl_time": latest_crawl_time,
        "count": len(items),
        "latest_count": len(latest_items),
        "items": items,
        "latest_items": latest_items,
        "platforms": platforms,
    }


def _read_rss(db_path: Optional[Path]) -> Dict[str, Any]:
    if not db_path or not db_path.exists():
        return {"date": None, "latest_crawl_time": None, "items": [], "feeds": []}

    date = db_path.stem
    with sqlite3.connect(db_path) as conn:
        latest_row = conn.execute(
            "SELECT crawl_time FROM rss_crawl_records ORDER BY crawl_time DESC LIMIT 1"
        ).fetchone()
        latest_crawl_time = latest_row[0] if latest_row else None

        feeds = _fetch_all(
            conn,
            """
            SELECT id, name, feed_url, is_active, last_fetch_time, last_fetch_status, item_count, updated_at
            FROM rss_feeds
            ORDER BY id
            """,
        )

        items = _fetch_all(
            conn,
            """
            SELECT
                r.id,
                r.title,
                r.feed_id,
                COALESCE(f.name, r.feed_id) AS feed_name,
                r.url,
                r.guid,
                r.published_at,
                r.summary,
                r.author,
                r.first_crawl_time,
                r.last_crawl_time,
                r.crawl_count,
                r.created_at,
                r.updated_at
            FROM rss_items r
            LEFT JOIN rss_feeds f ON f.id = r.feed_id
            ORDER BY r.last_crawl_time DESC, r.published_at DESC, r.feed_id ASC, r.id ASC
            """,
        )

    for item in items:
        item["is_latest"] = bool(latest_crawl_time and item.get("last_crawl_time") == latest_crawl_time)

    latest_items = [item for item in items if item["is_latest"]]
    return {
        "date": date,
        "latest_crawl_time": latest_crawl_time,
        "count": len(items),
        "latest_count": len(latest_items),
        "items": items,
        "latest_items": latest_items,
        "feeds": feeds,
    }


def _write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _compact_news_item(item: Dict[str, Any]) -> Dict[str, Any]:
    compact = {
        "id": item.get("item_id") or _item_ref("news", item),
        "t": item.get("title", ""),
        "cat": item.get("matched_category", ""),
        "src": item.get("platform_name") or item.get("platform_id", ""),
        "rank": item.get("rank"),
        "url": item.get("mobile_url") or item.get("url") or "",
        "time": item.get("last_crawl_time") or item.get("first_crawl_time") or "",
        "latest": bool(item.get("is_latest")),
        "type": "news",
    }
    return {key: value for key, value in compact.items() if value not in (None, "", [], {})}


def _compact_rss_item(item: Dict[str, Any]) -> Dict[str, Any]:
    compact = {
        "id": item.get("item_id") or _item_ref("rss", item),
        "t": item.get("title", ""),
        "cat": item.get("matched_category", ""),
        "src": item.get("feed_name") or item.get("feed_id", ""),
        "url": item.get("url") or "",
        "time": item.get("published_at") or item.get("last_crawl_time") or "",
        "latest": bool(item.get("is_latest")),
        "type": "rss",
    }
    summary = (item.get("summary") or "").strip()
    if summary:
        compact["summary"] = summary[:180]
    return {key: value for key, value in compact.items() if value not in (None, "", [], {})}


def _build_compact_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    items = [
        _compact_news_item(item)
        for item in payload.get("news", {}).get("items", [])
    ] + [
        _compact_rss_item(item)
        for item in payload.get("rss", {}).get("items", [])
    ]

    return {
        "schema_version": 1,
        "generated_at": payload.get("generated_at"),
        "date": payload.get("date"),
        "crawl_time": payload.get("crawl_time"),
        "counts": {
            "total": len(items),
            "news": payload.get("news", {}).get("count", 0),
            "rss": payload.get("rss", {}).get("count", 0),
        },
        "items": items,
    }


def _cleanup_old_date_dirs(base_dir: Path, keep_days: int = RETENTION_DAYS) -> List[Path]:
    """Remove output/json/YYYY-MM-DD directories older than the retention window."""
    if not base_dir.exists():
        return []

    today = _now_beijing().date()
    cutoff = today - timedelta(days=keep_days - 1)
    removed: List[Path] = []

    for child in base_dir.iterdir():
        if not child.is_dir():
            continue
        try:
            folder_date = datetime.strptime(child.name, DATE_FORMAT).date()
        except ValueError:
            continue
        if folder_date < cutoff:
            shutil.rmtree(child)
            removed.append(child)

    return removed


def main() -> int:
    news_db = _latest_db(NEWS_DIR)
    rss_db = _latest_db(RSS_DIR)

    news = _read_news(news_db)
    rss = _read_rss(rss_db)
    news, rss, categories = _apply_keyword_filter(news, rss)

    export_date = news.get("date") or rss.get("date") or _now_beijing().strftime(DATE_FORMAT)
    export_time = news.get("latest_crawl_time") or rss.get("latest_crawl_time") or _now_beijing().strftime("%H-%M")

    payload = {
        "schema_version": 2,
        "generated_at": _now_beijing().isoformat(),
        "source": {
            "repository": os.environ.get("GITHUB_REPOSITORY", ""),
            "run_id": os.environ.get("GITHUB_RUN_ID", ""),
            "run_number": os.environ.get("GITHUB_RUN_NUMBER", ""),
            "workflow": os.environ.get("GITHUB_WORKFLOW", ""),
            "ref": os.environ.get("GITHUB_REF_NAME", ""),
        },
        "date": export_date,
        "crawl_time": export_time,
        "counts": {
            "news": news.get("count", 0),
            "latest_news": news.get("latest_count", 0),
            "rss": rss.get("count", 0),
            "latest_rss": rss.get("latest_count", 0),
            "total": news.get("count", 0) + rss.get("count", 0),
            "latest_total": news.get("latest_count", 0) + rss.get("latest_count", 0),
            "raw_news": news.get("raw_count", 0),
            "raw_latest_news": news.get("raw_latest_count", 0),
            "raw_rss": rss.get("raw_count", 0),
            "raw_latest_rss": rss.get("raw_latest_count", 0),
        },
        "categories": categories,
        "news": news,
        "rss": rss,
    }

    compact_payload = _build_compact_payload(payload)

    latest_path = JSON_DIR / "latest.json"
    compact_latest_path = JSON_DIR / "latest.compact.json"
    daily_path = JSON_DIR / export_date / "news.json"
    compact_daily_path = JSON_DIR / export_date / "news.compact.json"

    _write_json(latest_path, payload)
    _write_json(compact_latest_path, compact_payload)
    _write_json(daily_path, payload)
    _write_json(compact_daily_path, compact_payload)
    removed_dirs = _cleanup_old_date_dirs(JSON_DIR)

    print(f"[export-json] news db: {news_db or 'not found'}")
    print(f"[export-json] rss db: {rss_db or 'not found'}")
    print(f"[export-json] wrote: {latest_path.relative_to(ROOT)}")
    print(f"[export-json] wrote: {compact_latest_path.relative_to(ROOT)}")
    print(f"[export-json] wrote: {daily_path.relative_to(ROOT)}")
    print(f"[export-json] wrote: {compact_daily_path.relative_to(ROOT)}")
    for removed_dir in removed_dirs:
        print(f"[export-json] removed old directory: {removed_dir.relative_to(ROOT)}")
    print(f"[export-json] total items: {payload['counts']['total']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
