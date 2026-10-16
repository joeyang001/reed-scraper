"""
Reed.co.uk Scraper — UK job listings.

Dependency-free (stdlib + Apify REST). Reads Reed's server-rendered Next.js
`__NEXT_DATA__` search payload (no browser, no API key):
  https://www.reed.co.uk/jobs/{keywords}-jobs?pageno=N
Normalized, de-duplicated, with provenance on every row.
"""
from __future__ import annotations
import json, os, re, ssl, uuid
from datetime import datetime, timezone
from urllib import request as urlrequest
from urllib.parse import urlencode, quote
from urllib.error import HTTPError, URLError

SCHEMA_VERSION = "1.0.0"
API = "https://api.apify.com/v2"
UA = {"User-Agent": "reed-scraper/1.0 (+https://apify.com)",
      "Accept": "text/html,application/xhtml+xml", "Accept-Language": "en-GB,en;q=0.9"}
_CTX = ssl.create_default_context()
HERE = os.path.dirname(os.path.abspath(__file__))
_NEXT = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)
_BASE = "https://www.reed.co.uk"
_SAL_PERIOD = {1: "hour", 2: "day", 3: "week", 4: "month", 5: "year"}


def log(*a):
    print(*a, flush=True)


def _u(path):
    return f"{API}{path}{'&' if '?' in path else '?'}" + urlencode({"token": os.environ.get("APIFY_TOKEN", "")})


def get_input():
    store = os.environ.get("ACTOR_DEFAULT_KEY_VALUE_STORE_ID")
    if store and os.environ.get("APIFY_TOKEN"):
        try:
            return json.loads(_get(_u(f"/key-value-stores/{store}/records/{os.environ.get('ACTOR_INPUT_KEY','INPUT')}")))
        except Exception as e:
            log(f"input fetch failed: {e}")
    if os.path.exists("input.json"):
        return json.load(open("input.json"))
    return {}


def push_items(items):
    token = os.environ.get("APIFY_TOKEN"); ds = os.environ.get("ACTOR_DEFAULT_DATASET_ID")
    if not (token and ds):
        with open("dataset_local.jsonl", "a") as f:
            for it in items:
                f.write(json.dumps(it) + "\n")
        return len(items)
    n = 0
    for i in range(0, len(items), 300):
        chunk = items[i:i + 300]
        req = urlrequest.Request(_u(f"/datasets/{ds}/items"), data=json.dumps(chunk).encode(),
                                 method="POST", headers={"Content-Type": "application/json"})
        urlrequest.urlopen(req, timeout=120, context=_CTX).read()
        n += len(chunk)
    return n


def charge(event_name, count):
    token = os.environ.get("APIFY_TOKEN"); rid = os.environ.get("ACTOR_RUN_ID")
    if not (token and rid) or count <= 0:
        return
    body = json.dumps({"eventName": event_name, "count": int(count)}).encode()
    req = urlrequest.Request(_u(f"/actor-runs/{rid}/charge"), data=body, method="POST",
                             headers={"Content-Type": "application/json", "idempotency-key": uuid.uuid4().hex})
    try:
        urlrequest.urlopen(req, timeout=30, context=_CTX).read()
    except HTTPError as e:
        try: log(f"charge {event_name} failed: {e.code} {e.read().decode()[:160]}")
        except Exception: log(f"charge {event_name} failed: {e.code}")
    except Exception as e:
        log(f"charge {event_name} failed: {e}")


def _get(url, timeout=35):
    with urlrequest.urlopen(urlrequest.Request(url, headers=UA), timeout=timeout, context=_CTX) as r:
        return r.read().decode("utf-8", "ignore")


def _now():
    return datetime.now(timezone.utc).isoformat()


def fetch_jobs(url):
    h = _get(url)
    m = _NEXT.search(h)
    if not m:
        return [], 0
    sr = json.loads(m.group(1))["props"]["pageProps"].get("searchResults") or {}
    return (sr.get("jobs") or []), (sr.get("count") or 0)


def parse_job(item, search_url, search_term, page):
    j = item.get("jobDetail") or {}
    url = item.get("url") or ""
    url = url if url.startswith("http") else (_BASE + url if url else None)
    return {
        "job_id": str(j.get("jobId")) if j.get("jobId") is not None else None,
        "title": j.get("jobTitle"),
        "employer": j.get("ouName"),
        "employer_id": str(j.get("ouId")) if j.get("ouId") is not None else None,
        "employer_type": j.get("ouType"),
        "location": j.get("displayLocationName"),
        "county": j.get("countyLocation"),
        "salary_from": j.get("salaryFrom"),
        "salary_to": j.get("salaryTo"),
        "salary_currency": "GBP" if j.get("salaryCurrencyId") in (1, None) else str(j.get("salaryCurrencyId")),
        "salary_period": _SAL_PERIOD.get(j.get("salaryType")),
        "salary_type_code": j.get("salaryType"),
        "working_option": j.get("workingOption"),
        "is_full_time": j.get("isFullTime"),
        "is_part_time": j.get("isPartTime"),
        "category": j.get("taxonomyLevel1"),
        "subcategory": j.get("taxonomyLevel2"),
        "description_snippet": j.get("jobDescriptionSnippet"),
        "date_posted": j.get("dateCreated"),
        "display_date": j.get("displayDate"),
        "expiry_date": j.get("expiryDate"),
        "is_easy_apply": j.get("isEasyApply"),
        "is_promoted": j.get("isPromoted"),
        "applicant_count": j.get("applicantCount"),
        "url": url,
        "page": page,
        "search_term": search_term,
        "search_url": search_url,
        "schema_version": SCHEMA_VERSION,
        "fetched_at": _now(),
    }


def build_targets(inp):
    targets = []
    for u in (inp.get("searchUrls") or []):
        if u:
            targets.append((u, None))
    kws = inp.get("keywords")
    if isinstance(kws, str):
        kws = [kws]
    for kw in (kws or []):
        kw = str(kw).strip()
        if kw:
            path = quote(kw.replace(" ", "+"))
            targets.append((f"{_BASE}/jobs/{path}-jobs", kw))
    if not targets:
        targets = [(f"{_BASE}/jobs/software-engineer-jobs", "software engineer")]
    return targets


def main():
    inp = get_input() or {}
    targets = build_targets(inp)
    max_pages = int(inp.get("maxPages") or 3)
    max_jobs = int(inp.get("maxJobs") or 100000)
    seen = set(); rows = []; errors = []; pages_ok = 0
    charge("actor-start", 1)
    for base, term in targets:
        for page in range(1, max_pages + 1):
            sep = "&" if "?" in base else "?"
            u = f"{base}{sep}pageno={page}"
            try:
                jobs, count = fetch_jobs(u)
                pages_ok += 1
                if not jobs:
                    break
                for it in jobs:
                    r = parse_job(it, base, term, page)
                    k = r.get("job_id") or r.get("url")
                    if k and k not in seen:
                        seen.add(k); rows.append(r)
                if page * 25 >= count:
                    break
            except (HTTPError, URLError, ValueError, KeyError) as e:
                errors.append(f"{u[:60]}: {str(e)[:60]}")
                break
    rows = rows[:max_jobs]
    pushed = push_items(rows)
    charge("job", len(rows))
    log(f"FINISHED pages_ok={pages_ok} pushed={pushed} errors={len(errors)}")
    if errors:
        log("Errors: " + "; ".join(errors[:15]))


if __name__ == "__main__":
    main()
