# Reed.co.uk Scraper — UK Jobs, Salaries & Details

**Scrape Reed.co.uk — one of the UK's biggest job boards — into a clean, normalized, de-duplicated dataset.**

Get job title, employer, location, **salary range and period**, **working option (remote / hybrid / on-site)**, full/part-time, category & subcategory, description snippet, posting date, expiry date and the direct apply link. Paginated across any keyword search.

> Perfect for UK job-market analysis, recruiting/sourcing pipelines, salary benchmarking and lead-gen.

## What you get

- **Jobs from any Reed search** — pass keywords or full search URLs.
- **Normalized fields** — numeric `salary_from`/`salary_to`, `salary_period` (hour/day/week/month/year), `working_option`, `is_full_time`/`is_part_time`.
- **Structure** — `category` + `subcategory`, `employer`, county + city, posting/expiry dates.
- **Signals** — `is_promoted`, `is_easy_apply`.
- **De-duplicated** by job id, with provenance (`search_url`, `page`, `fetched_at`, `schema_version`).

## Output fields (30 per row)

`job_id`, `title`, `employer`, `employer_id`, `employer_type`, `location`, `county`, `salary_from`, `salary_to`, `salary_currency`, `salary_period`, `salary_type_code`, `working_option`, `is_full_time`, `is_part_time`, `category`, `subcategory`, `description_snippet`, `date_posted`, `display_date`, `expiry_date`, `is_easy_apply`, `is_promoted`, `applicant_count`, `url`, `page`, `search_term`, `search_url`, `schema_version`, `fetched_at`.

### Sample row

```json
{
  "job_id": "57336518",
  "title": "Software Engineer",
  "employer": "IBM SIXworks Limited",
  "location": "Cheltenham",
  "county": "Gloucestershire",
  "salary_from": 55000,
  "salary_to": 70000,
  "salary_currency": "GBP",
  "salary_period": "year",
  "working_option": "hybrid",
  "is_full_time": true,
  "category": "Engineer",
  "subcategory": "Software Engineer",
  "date_posted": "2026-09-11T12:42:59",
  "url": "https://www.reed.co.uk/jobs/software-engineer/57336518",
  "schema_version": "1.0.0",
  "fetched_at": "2026-10-16T04:10:00+00:00"
}
```

## Input

- **Keywords** — e.g. `["software engineer", "data analyst"]`.
- **Search URLs** — paste any Reed.co.uk search URL.
- **Max pages** per search (25 jobs/page), **Max jobs** total.

## Use cases

- **Recruiting & sourcing** — build role lists by title, location, salary.
- **Salary benchmarking** — analyze UK pay by role and region.
- **Job-board aggregation** — feed fresh listings into your product.
- **Lead-gen** — companies hiring = buying signals.

## Pricing

Pay per result — **$0.70 per 1,000 jobs** (+ $0.005 per run start). Only pay for jobs returned. Free plan covers testing.

## Notes

- Public Reed.co.uk job data only; no login.
- Only fields Reed publishes are captured; missing values are returned as `null`.
