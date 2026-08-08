#!/usr/bin/env python3
"""Build the private, local SKH website maintenance dashboard."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import html
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

try:
    import yaml
except ImportError as exc:
    raise SystemExit(
        "PyYAML is required. Open the dashboard with 'Open SKH Dashboard.command' "
        "so it can prepare the dependency automatically."
    ) from exc


REPO = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO / ".maintenance"
OUTPUT_FILE = OUTPUT_DIR / "dashboard.html"
CACHE_FILE = OUTPUT_DIR / "link-cache.json"
BANGKOK = ZoneInfo("Asia/Bangkok")
TODAY = dt.datetime.now(BANGKOK).date()
NOW = dt.datetime.now(BANGKOK)

TEXT_SUFFIXES = {
    ".html", ".md", ".yml", ".yaml", ".css", ".js", ".json", ".xml",
    ".txt", ".py", ".qmd", ".scss", ".lua",
}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"}
SKIP_SCAN_PARTS = {".git", ".maintenance", "_site", "site_libs", "_to_delete"}
URL_RE = re.compile(r"https?://[^\s<>\"'`]+")
CACHE_SCHEMA = 4


@dataclass
class Finding:
    severity: str
    title: str
    detail: str
    file: str = ""


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def rel(path: Path) -> str:
    try:
        return path.relative_to(REPO).as_posix()
    except ValueError:
        return str(path)


def load_yaml(path: Path, default: Any = None) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            value = yaml.safe_load(handle)
            return default if value is None else value
    except (OSError, yaml.YAMLError) as exc:
        return {"__error__": str(exc)}


def front_matter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        metadata = yaml.safe_load(parts[1]) or {}
        return metadata if isinstance(metadata, dict) else {}, parts[2]
    except yaml.YAMLError:
        return {}, parts[2]


def as_date(value: Any) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if value:
        try:
            return dt.date.fromisoformat(str(value)[:10])
        except ValueError:
            return None
    return None


def check_posts() -> tuple[list[dict[str, Any]], list[Finding]]:
    scheduled: list[dict[str, Any]] = []
    findings: list[Finding] = []
    for path in sorted((REPO / "_posts").glob("*.md")):
        meta, _ = front_matter(path)
        publish_date = as_date(meta.get("date"))
        missing = [key for key in ("title", "date", "description", "tag", "kind") if not meta.get(key)]
        if meta.get("kind") == "essay" and not meta.get("series"):
            missing.append("series")
        if missing:
            findings.append(Finding(
                "warning", f"ข้อมูลบทความไม่ครบ: {meta.get('title') or path.name}",
                "ขาด " + ", ".join(missing), rel(path),
            ))
        image = meta.get("image")
        if image:
            image_path = REPO / str(image).lstrip("/")
            if not image_path.exists():
                findings.append(Finding(
                    "critical", f"ไม่พบภาพของบทความ: {meta.get('title') or path.name}",
                    str(image), rel(path),
                ))
        if publish_date and publish_date > TODAY:
            scheduled.append({
                "title": meta.get("title", path.stem),
                "date": publish_date,
                "days": (publish_date - TODAY).days,
                "kind": meta.get("kind", "—"),
                "image": "พร้อม" if image and (REPO / str(image).lstrip("/")).exists() else "ยังไม่มี",
                "file": rel(path),
            })
    scheduled.sort(key=lambda item: item["date"])
    return scheduled, findings


def check_people() -> tuple[dict[str, int], list[Finding]]:
    path = REPO / "_data/people.yml"
    people = load_yaml(path, [])
    findings: list[Finding] = []
    counts = {"current": 0, "alumni": 0}
    if isinstance(people, dict) and people.get("__error__"):
        findings.append(Finding("critical", "อ่านข้อมูลสมาชิกไม่ได้", people["__error__"], rel(path)))
        return counts, findings
    if not isinstance(people, list):
        findings.append(Finding("critical", "รูปแบบข้อมูลสมาชิกไม่ถูกต้อง", "ควรเป็นรายการ YAML", rel(path)))
        return counts, findings

    seen: set[str] = set()
    for person in people:
        if not isinstance(person, dict) or person.get("status") == "example":
            continue
        name = str(person.get("name") or "ไม่ระบุชื่อ")
        key = name.casefold()
        if key in seen:
            findings.append(Finding("critical", f"ชื่อสมาชิกซ้ำ: {name}", "พบมากกว่าหนึ่งรายการ", rel(path)))
        seen.add(key)
        status = person.get("status")
        if status == "current":
            counts["current"] += 1
            required = ("level", "role", "since", "topic", "photo")
        elif status == "alumnus":
            counts["alumni"] += 1
            required = ("photo",)
            if not any(person.get(key) for key in ("deng", "meng", "postdoc")):
                findings.append(Finding("warning", f"ไม่พบประเภทศิษย์เก่า: {name}", "ขาด deng, meng หรือ postdoc", rel(path)))
        else:
            required = ()
            findings.append(Finding("warning", f"สถานะสมาชิกไม่รู้จัก: {name}", str(status), rel(path)))
        missing = [field for field in required if not person.get(field)]
        if missing:
            findings.append(Finding(
                "warning", f"ข้อมูลสมาชิกไม่ครบ: {name}",
                "ขาด " + ", ".join(missing), rel(path),
            ))
        photo = person.get("photo")
        if photo and not (REPO / "img/people" / str(photo)).exists():
            findings.append(Finding("critical", f"ไม่พบรูปสมาชิก: {name}", str(photo), rel(path)))
        link = str(person.get("link") or "")
        if "0000-0000-0000-0000" in link:
            findings.append(Finding("warning", f"ORCID ยังเป็นตัวอย่าง: {name}", link, rel(path)))
    return counts, findings


def source_texts() -> list[tuple[Path, str]]:
    texts: list[tuple[Path, str]] = []
    for path in REPO.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in SKIP_SCAN_PARTS for part in path.relative_to(REPO).parts):
            continue
        try:
            texts.append((path, path.read_text(encoding="utf-8", errors="ignore")))
        except OSError:
            pass
    return texts


def image_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        from PIL import Image
        with Image.open(path) as image:
            return image.size
    except Exception:
        return None


def check_images(texts: list[tuple[Path, str]]) -> tuple[list[dict[str, Any]], list[Finding]]:
    joined = "\n".join(text for _, text in texts)
    unused: list[dict[str, Any]] = []
    findings: list[Finding] = []
    roots = [REPO / "img", REPO / "covers"]
    for root in roots:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            relative = rel(path)
            if path.name == "_placeholder.jpg":
                continue
            referenced = relative in joined or path.name in joined
            size = path.stat().st_size
            dims = image_dimensions(path)
            if not referenced:
                unused.append({
                    "file": relative,
                    "size": f"{size / 1024:.0f} KB",
                    "dimensions": f"{dims[0]}×{dims[1]}" if dims else "—",
                })
            if size > 1_500_000:
                findings.append(Finding(
                    "warning", f"รูปมีขนาดใหญ่: {relative}",
                    f"{size / 1024 / 1024:.1f} MB" + (f", {dims[0]}×{dims[1]} px" if dims else ""), relative,
                ))

    # Find common local image references whose targets do not exist.
    patterns = [
        re.compile(r"(?:src|href)=[\"'](?:\{\{[^}]+\}\})?/?([^\"'#?]+\.(?:jpe?g|png|webp|gif|svg))", re.I),
        re.compile(r"(?:image|photo|file):\s*[\"']?/?([^\s\"']+\.(?:jpe?g|png|webp|gif|svg))", re.I),
    ]
    missing_seen: set[str] = set()
    for source, text in texts:
        source_parts = source.relative_to(REPO).parts
        # Only scan files that become part of the published site. Maintenance
        # guides and generator source contain intentional example filenames.
        if source.suffix.lower() == ".md" and (not source_parts or source_parts[0] != "_posts"):
            continue
        if source_parts and source_parts[0] in {"tools", "_teaching-src"}:
            continue
        for pattern in patterns:
            for match in pattern.finditer(text):
                raw = match.group(1).replace("{{ site.baseurl }}/", "").lstrip("/")
                # Liquid expressions are resolved during the Jekyll build and
                # cannot be treated as literal filenames here.
                if "{{" in raw or "{%" in raw or "}}" in raw or "%}" in raw:
                    continue
                candidates = [REPO / raw, source.parent / raw]
                if source.name == "people.yml" and "/" not in raw:
                    candidates.append(REPO / "img/people" / raw)
                if source.name == "activities.yml" and "/" not in raw:
                    candidates.append(REPO / "img/activities" / raw)
                if source.name == "covers.yml" and "/" not in raw:
                    candidates.append(REPO / "covers" / raw)
                if source.name == "collaborators.yml" and "/" not in raw:
                    candidates.append(REPO / "img/collaborators" / raw)
                if raw in {"example-person.jpg", "full-name.jpg"}:
                    continue
                if not any(candidate.exists() for candidate in candidates) and raw not in missing_seen:
                    missing_seen.add(raw)
                    findings.append(Finding("critical", f"อ้างถึงรูปที่ไม่มีไฟล์: {raw}", "ตรวจ path หรือเพิ่มไฟล์", rel(source)))
    return unused, findings


MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}


def check_publications() -> tuple[dict[str, Any], list[Finding]]:
    path = REPO / "index.html"
    text = path.read_text(encoding="utf-8")
    metrics_match = re.search(
        r"([\d,]+) publications\s*[·&middot;]+\s*([\d,]+) citations\s*[·&middot;]+\s*h-index\s*([\d,]+)",
        text, re.I,
    )
    date_match = re.search(
        r"Scopus Author ID[^,.]*,\s*(January|February|March|April|May|June|July|August|September|October|November|December)\s+(20\d{2})",
        text, re.I,
    )
    result: dict[str, Any] = {"publications": "—", "citations": "—", "h_index": "—", "checked": "ไม่พบ", "age_days": None}
    findings: list[Finding] = []
    if metrics_match:
        result.update({"publications": metrics_match.group(1), "citations": metrics_match.group(2), "h_index": metrics_match.group(3)})
    else:
        findings.append(Finding("critical", "อ่านตัวเลขผลงานไม่ได้", "ไม่พบรูปแบบ publications · citations · h-index", rel(path)))
    if date_match:
        month = MONTHS[date_match.group(1).lower()]
        checked = dt.date(int(date_match.group(2)), month, 1)
        age = (TODAY - checked).days
        result.update({"checked": checked.strftime("%B %Y"), "age_days": age})
        if age >= 365:
            findings.append(Finding("critical", "ตัวเลขผลงานเกินหนึ่งปีแล้ว", f"ตรวจล่าสุด {age} วันก่อน", rel(path)))
        elif age >= 180:
            findings.append(Finding("warning", "ถึงเวลาตรวจตัวเลขผลงาน", f"ตรวจล่าสุด {age} วันก่อน", rel(path)))
    else:
        findings.append(Finding("warning", "ไม่พบวันที่ตรวจตัวเลขผลงาน", "ควรระบุ Month YYYY หลัง Scopus Author ID", rel(path)))
    return result, findings


def extract_urls(texts: Iterable[tuple[Path, str]]) -> dict[str, set[str]]:
    urls: dict[str, set[str]] = {}
    for path, text in texts:
        parts = path.relative_to(REPO).parts
        if len(parts) == 1 and path.suffix.lower() not in {".html", ".txt", ".xml", ".yml", ".yaml"}:
            continue
        if parts and parts[0] in {"tools", "_teaching-src", ".github"}:
            continue
        for raw in URL_RE.findall(text):
            url = raw.rstrip(".,;:")
            # Remove Markdown/HTML closing punctuation while preserving balanced
            # parentheses that legitimately occur inside a URL.
            while url.endswith(")") and url.count(")") > url.count("("):
                url = url[:-1]
            url = url.rstrip("]}")
            if (
                "example.com" in url
                or "0000-0000-0000-0000" in url
                or "{{" in url
                or "{%" in url
                or url in {"https://fonts.googleapis.com", "https://fonts.gstatic.com"}
            ):
                continue
            urls.setdefault(url, set()).add(rel(path))
    return urls


def read_link_cache() -> dict[str, Any]:
    try:
        payload = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        if payload.get("schema") != CACHE_SCHEMA:
            return {}
        links = payload.get("links")
        return links if isinstance(links, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def probe_url(url: str) -> dict[str, Any]:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; SKH-Maintenance/1.0)"}
    request = urllib.request.Request(url, headers=headers, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            code = response.getcode() or 200
            final = response.geturl()
            return {"code": code, "status": "ok", "final": final, "error": "", "checked": NOW.isoformat()}
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 405, 406, 429, 999):
            # These commonly reject automated HEAD requests but are not broken links.
            return {"code": exc.code, "status": "blocked", "final": url, "error": str(exc.reason), "checked": NOW.isoformat()}
        # Some publishers and DOI targets mishandle HEAD. Confirm with a small
        # GET before reporting the link as genuinely broken.
        get_request = urllib.request.Request(
            url, headers={**headers, "Range": "bytes=0-1023"}, method="GET",
        )
        try:
            with urllib.request.urlopen(get_request, timeout=10) as response:
                code = response.getcode() or 200
                return {"code": code, "status": "ok", "final": response.geturl(), "error": "", "checked": NOW.isoformat()}
        except urllib.error.HTTPError as get_exc:
            if get_exc.code in (403, 405, 406, 429, 999):
                return {"code": get_exc.code, "status": "blocked", "final": url, "error": str(get_exc.reason), "checked": NOW.isoformat()}
            return {"code": get_exc.code, "status": "broken", "final": url, "error": str(get_exc.reason), "checked": NOW.isoformat()}
        except Exception as get_exc:
            return {"code": 0, "status": "timeout", "final": url, "error": str(get_exc)[:160], "checked": NOW.isoformat()}
    except Exception as exc:
        return {"code": 0, "status": "timeout", "final": url, "error": str(exc)[:160], "checked": NOW.isoformat()}


def check_links(texts: list[tuple[Path, str]], skip: bool) -> tuple[list[dict[str, Any]], list[Finding]]:
    urls = extract_urls(texts)
    cache = read_link_cache()
    max_age = dt.timedelta(days=7)
    to_check: list[str] = []
    results: dict[str, Any] = {}
    for url in urls:
        cached = cache.get(url)
        fresh = False
        if cached and cached.get("checked"):
            try:
                fresh = NOW - dt.datetime.fromisoformat(cached["checked"]) < max_age
            except (ValueError, TypeError):
                pass
        if cached and (fresh or skip):
            results[url] = cached
        elif not skip:
            to_check.append(url)

    if to_check:
        print(f"Checking {len(to_check)} external links (cached for 7 days)...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            future_map = {pool.submit(probe_url, url): url for url in to_check}
            for future in concurrent.futures.as_completed(future_map):
                url = future_map[future]
                results[url] = future.result()
        cache.update(results)
        CACHE_FILE.write_text(
            json.dumps({"schema": CACHE_SCHEMA, "links": cache}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        CACHE_FILE.chmod(0o600)

    rows: list[dict[str, Any]] = []
    findings: list[Finding] = []
    for url in sorted(urls):
        result = results.get(url)
        if not result:
            continue
        status = result.get("status", "timeout")
        if status not in ("ok",):
            rows.append({
                "url": url,
                "status": status,
                "code": result.get("code") or "—",
                "detail": result.get("error") or "",
                "files": ", ".join(sorted(urls[url])[:3]),
            })
            if status == "broken":
                findings.append(Finding("critical", "ลิงก์ภายนอกเสีย", f"HTTP {result.get('code')}: {url}", sorted(urls[url])[0]))
            elif status == "timeout":
                findings.append(Finding("warning", "ตรวจลิงก์ไม่ได้", url, sorted(urls[url])[0]))
    if CACHE_FILE.exists():
        CACHE_FILE.chmod(0o600)
    return rows, findings


def finding_rows(findings: list[Finding]) -> str:
    if not findings:
        return '<div class="empty">ไม่พบสิ่งที่ต้องจัดการ</div>'
    order = {"critical": 0, "warning": 1, "info": 2}
    findings = sorted(findings, key=lambda item: (order.get(item.severity, 9), item.title.casefold()))
    return "".join(
        f'<tr><td><span class="badge {esc(item.severity)}">{esc({"critical":"ต้องแก้", "warning":"ควรตรวจ", "info":"ข้อมูล"}.get(item.severity, item.severity))}</span></td>'
        f'<td><strong>{esc(item.title)}</strong><div class="muted">{esc(item.detail)}</div></td>'
        f'<td><code>{esc(item.file or "—")}</code></td></tr>'
        for item in findings
    )


def render_dashboard(
    scheduled: list[dict[str, Any]], people: dict[str, int], unused: list[dict[str, Any]],
    publications: dict[str, Any], link_rows: list[dict[str, Any]], findings: list[Finding],
    links_skipped: bool,
) -> str:
    critical = sum(item.severity == "critical" for item in findings)
    warnings = sum(item.severity == "warning" for item in findings)
    health = "ต้องแก้ไข" if critical else ("ควรตรวจ" if warnings else "เรียบร้อย")
    health_class = "critical" if critical else ("warning" if warnings else "good")

    scheduled_rows = "".join(
        f'<tr><td><strong>{esc(item["title"])}</strong><div class="muted"><code>{esc(item["file"])}</code></div></td>'
        f'<td>{esc(item["date"].isoformat())}</td><td>{esc(item["days"])} วัน</td><td>{esc(item["kind"])}</td><td>{esc(item["image"])}</td></tr>'
        for item in scheduled
    ) or '<tr><td colspan="5" class="empty">ไม่มีบทความที่รอเผยแพร่</td></tr>'

    unused_rows = "".join(
        f'<tr><td><code>{esc(item["file"])}</code></td><td>{esc(item["dimensions"])}</td><td>{esc(item["size"])}</td></tr>'
        for item in unused[:100]
    ) or '<tr><td colspan="3" class="empty">ไม่พบรูปที่ไม่ได้ใช้งาน</td></tr>'

    links_body = "".join(
        f'<tr><td><span class="badge {"critical" if item["status"] == "broken" else "warning"}">{esc(item["status"])}</span></td>'
        f'<td><a href="{esc(item["url"])}" target="_blank" rel="noopener">{esc(item["url"])}</a><div class="muted">{esc(item["detail"])}</div></td>'
        f'<td>{esc(item["code"])}</td><td><code>{esc(item["files"])}</code></td></tr>'
        for item in link_rows
    ) or f'<tr><td colspan="4" class="empty">{"ข้ามการตรวจลิงก์ในการทดสอบครั้งนี้" if links_skipped else "ลิงก์ที่ตรวจผ่านทั้งหมด"}</td></tr>'

    return f'''<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>SKH Maintenance Dashboard</title>
<style>
:root{{--ink:#17333f;--muted:#657780;--paper:#f4f2ec;--card:#fff;--line:#dfe3df;--teal:#0e6b6f;--amber:#bb7419;--red:#a13d36;--green:#347253}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
.wrap{{max-width:1180px;margin:auto;padding:42px 24px 72px}} header{{display:flex;justify-content:space-between;gap:24px;align-items:end;margin-bottom:28px}}
.eyebrow{{font-size:12px;font-weight:700;letter-spacing:.13em;text-transform:uppercase;color:var(--teal)}} h1{{font:700 clamp(30px,4vw,50px)/1.05 Georgia,serif;margin:7px 0 4px}} h2{{font:700 24px/1.2 Georgia,serif;margin:0}}
.muted{{color:var(--muted);font-size:13px;margin-top:3px}} .private{{background:#e4eeea;border:1px solid #c5d8cf;border-radius:999px;padding:7px 12px;font-size:12px;font-weight:700;white-space:nowrap}}
.summary{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:22px 0 28px}} .card,.panel{{background:var(--card);border:1px solid var(--line);border-radius:14px;box-shadow:0 2px 10px #17333f08}}
.card{{padding:17px}} .card .number{{font:700 29px/1.05 Georgia,serif;margin:5px 0}} .card .label{{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.06em}}
.status.good{{color:var(--green)}} .status.warning{{color:var(--amber)}} .status.critical{{color:var(--red)}} .panel{{margin-top:16px;overflow:hidden}} .panel-head{{display:flex;justify-content:space-between;gap:20px;align-items:center;padding:20px 22px;border-bottom:1px solid var(--line)}}
.panel-body{{padding:0 22px 22px;overflow:auto}} table{{border-collapse:collapse;width:100%;min-width:700px}} th{{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.08em;text-align:left;padding:13px 10px;border-bottom:1px solid var(--line)}} td{{vertical-align:top;padding:13px 10px;border-bottom:1px solid #edf0ed}} tr:last-child td{{border-bottom:0}} code{{font:12px ui-monospace,SFMono-Regular,Menlo,monospace;color:#3f555f}} a{{color:var(--teal);word-break:break-word}}
.badge{{display:inline-block;border-radius:999px;padding:3px 8px;font-size:11px;font-weight:700;white-space:nowrap}} .badge.critical{{background:#f8e4e1;color:var(--red)}} .badge.warning{{background:#faedd8;color:#8c5815}} .badge.info{{background:#e5eef1;color:#3b6473}} .empty{{color:var(--muted);padding:24px 10px;text-align:center}} details summary{{cursor:pointer;list-style:none}} details summary::-webkit-details-marker{{display:none}} details summary:after{{content:"เปิดดู";font-size:12px;color:var(--teal);font-weight:700}} details[open] summary:after{{content:"ซ่อน"}}
.footer{{margin-top:28px;color:var(--muted);font-size:12px}} @media(max-width:850px){{.summary{{grid-template-columns:repeat(2,1fr)}}header{{align-items:start;flex-direction:column}}}} @media(max-width:520px){{.wrap{{padding:26px 14px 56px}}.summary{{grid-template-columns:1fr 1fr}}}}
</style>
</head>
<body><main class="wrap">
<header><div><div class="eyebrow">SKH Research Group</div><h1>Maintenance Dashboard</h1><div class="muted">ตรวจเมื่อ {esc(NOW.strftime("%d %B %Y, %H:%M"))} · Asia/Bangkok</div></div><div class="private">เฉพาะในเครื่องนี้ · ไม่ได้เผยแพร่</div></header>
<section class="summary">
  <div class="card"><div class="label">สถานะรวม</div><div class="number status {health_class}">{esc(health)}</div><div class="muted">{critical} ต้องแก้ · {warnings} ควรตรวจ</div></div>
  <div class="card"><div class="label">รอเผยแพร่</div><div class="number">{len(scheduled)}</div><div class="muted">บทความตามกำหนด</div></div>
  <div class="card"><div class="label">สมาชิกปัจจุบัน</div><div class="number">{people["current"]}</div><div class="muted">ศิษย์เก่า {people["alumni"]} คน</div></div>
  <div class="card"><div class="label">รูปที่อาจไม่ได้ใช้</div><div class="number">{len(unused)}</div><div class="muted">ตรวจทานก่อนลบ</div></div>
  <div class="card"><div class="label">ตัวเลข Scopus</div><div class="number">{esc(publications["publications"])}</div><div class="muted">ตรวจล่าสุด {esc(publications["checked"])}</div></div>
</section>

<section class="panel"><div class="panel-head"><div><h2>สิ่งที่ต้องจัดการ</h2><div class="muted">เรียงรายการสำคัญก่อน</div></div></div><div class="panel-body"><table><thead><tr><th>ระดับ</th><th>รายการ</th><th>ไฟล์</th></tr></thead><tbody>{finding_rows(findings)}</tbody></table></div></section>

<section class="panel"><div class="panel-head"><div><h2>บทความที่รอเผยแพร่</h2><div class="muted">วันที่เทียบตามเขตเวลา Asia/Bangkok</div></div></div><div class="panel-body"><table><thead><tr><th>บทความ</th><th>วันที่</th><th>เหลือ</th><th>ประเภท</th><th>ภาพ</th></tr></thead><tbody>{scheduled_rows}</tbody></table></div></section>

<details class="panel"><summary class="panel-head"><div><h2>รูปที่อาจไม่ได้ใช้งาน</h2><div class="muted">{len(unused)} ไฟล์ · ตรวจทานก่อนลบ เพราะบางไฟล์อาจถูกใช้งานจากภายนอก</div></div></summary><div class="panel-body"><table><thead><tr><th>ไฟล์</th><th>ขนาดภาพ</th><th>ขนาดไฟล์</th></tr></thead><tbody>{unused_rows}</tbody></table></div></details>

<details class="panel"><summary class="panel-head"><div><h2>ลิงก์ที่ต้องตรวจทาน</h2><div class="muted">ผลตรวจเก็บไว้ 7 วัน · blocked ไม่ได้แปลว่าลิงก์เสีย</div></div></summary><div class="panel-body"><table><thead><tr><th>สถานะ</th><th>ลิงก์</th><th>HTTP</th><th>พบใน</th></tr></thead><tbody>{links_body}</tbody></table></div></details>

<section class="panel"><div class="panel-head"><div><h2>ตัวเลขผลงาน</h2><div class="muted">เตือนทุก 6 เดือนจากวันที่ที่ระบุในหน้า Publications</div></div></div><div class="panel-body"><table><thead><tr><th>Publications</th><th>Citations</th><th>h-index</th><th>ตรวจล่าสุด</th><th>อายุข้อมูล</th></tr></thead><tbody><tr><td>{esc(publications["publications"])}</td><td>{esc(publications["citations"])}</td><td>{esc(publications["h_index"])}</td><td>{esc(publications["checked"])}</td><td>{esc(str(publications["age_days"]) + " วัน" if publications["age_days"] is not None else "—")}</td></tr></tbody></table></div></section>

<div class="footer">รายงานนี้สร้างจากไฟล์ในเครื่องและอยู่ที่ <code>.maintenance/dashboard.html</code> เท่านั้น การลบรายงานไม่มีผลต่อเว็บไซต์</div>
</main></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-links", action="store_true", help="Do not make network requests (for offline testing).")
    args = parser.parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.chmod(0o700)

    print("Reading posts, people, images, and publication metrics...")
    texts = source_texts()
    scheduled, post_findings = check_posts()
    people, people_findings = check_people()
    unused, image_findings = check_images(texts)
    publications, publication_findings = check_publications()
    link_rows, link_findings = check_links(texts, args.skip_links)
    findings = post_findings + people_findings + image_findings + publication_findings + link_findings

    dashboard = render_dashboard(
        scheduled, people, unused, publications, link_rows, findings, args.skip_links,
    )
    OUTPUT_FILE.write_text(dashboard, encoding="utf-8")
    OUTPUT_FILE.chmod(0o600)
    print(f"Dashboard ready: {OUTPUT_FILE}")
    print(f"Findings: {sum(f.severity == 'critical' for f in findings)} critical, {sum(f.severity == 'warning' for f in findings)} warnings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
