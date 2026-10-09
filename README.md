# ScholarScope

## Journal Explorer — 2026-10-10

`explorer/` is the journal dossier within the existing Publish desk, linked from
the main header and each journal detail. No new standalone research product.

- **2,033 registry journal identities**, **1,853 with corpus records**, **1,738,096
  article/review records** derived from the existing Research Book. JOB has 2,859.
- Annual output, title-topic heatmap, share/momentum bubble plot, publisher opportunity
  calendar, evidence links, 12/24-month qualitative outlooks, recent article search.
- **Journal of Organizational Behavior is the only fully reviewed editorial pilot.**
  Its 4 calls, October 2026 issue, editor, author instructions and 2025 timing metrics
  were checked on publisher pages on 2026-10-10. Deadline/policy discrepancies remain
  explicit. Other journals have corpus exploration and planning, not fabricated calls.
- 100 saved Crossref records; 4 selected Early View DOIs verified against Crossref
  and the publisher listing. Live refresh checks ISSNs. Separate live Crossref preprint
  search labels records as unreviewed leads, never inferred journal submissions.
- Backward planner: route, stage, durations, deadline conflicts, per-journal local
  saving (`ss_explorer_plan_<id>`), milestones, readiness checks, Markdown and ICS
  exports, conditional acceptance/publication scenarios, Throughline topic handoff.
- Forecasts are **uncalibrated editorial-fit inferences**, never acceptance probabilities.
  Topic lenses are transparent overlapping title regexes, not validated constructs.
  Momentum compares 2022–23 vs 2024–25 shares; excludes partial 2026. Minimum 40
  records in each window and 5 recent title matches. No significance is implied.
  Complete calendar years do not imply complete publisher coverage.

### Rebuild / verify

```text
python scripts/build-explorer.py
python scripts/refresh-explorer.py
node scripts/verify-explorer.mjs
python -m http.server 8771 --bind 127.0.0.1
# In a second terminal; EXPLORER_TEST_URL defaults to port 8768, so set it to 8771:
python scripts/smoke-explorer.py
```

The corpus builder reads sibling `syeds-research-book/data/` without modifying it.
Identity prefers unambiguous exact-ISSN-backed source IDs, then unique normalized
registry titles; source IDs shared by renamed journals are not assigned arbitrarily.
Generated files total approximately 20 MB and load one journal at a time. Dates in
the builder describe the reviewed release; update them when rebuilding from a new
release. Publisher calls in `explorer/data/job-editorial.json` require human review;
Crossref refresh does **not** refresh those or the historical corpus.

Browser verification covers journal switching, mobile overflow, exact publisher-call
selection, proposal vs paper schedules, local save/reload, deadline warnings, failed
refresh retention, paper filtering and actual file exports. Live browser Crossref
refresh and posted-content search also passed. Screenshots and QA exports live in
`../output/journal-explorer/` (outside the served repository).

This is buildless; existing GitHub Pages deployment serves `/explorer/`.

A live directory of the **institutions, schools, journals, and authors** that lead
**social science & management** research — part of the Research Suite (reference tier).

Single-file app (`index.html`, no build). All data is fetched live from
[OpenAlex](https://openalex.org) in the browser (anonymous, CORS) — **nothing is
invented**; every entity and number is a real OpenAlex record, with links out
(OpenAlex / ROR / ORCID / DOI) to verify.

## What it does
- **🏆 Leaders** — pick a field (Psychology · Sociology · Economics · Political science ·
  Business, or search any OpenAlex concept) and see the ranked leaders:
  - *Institutions* — most prolific in the field (`group_by=institutions.id`).
  - *Authors* — highest-impact, ranked by count of highly-cited works (cited 200+),
    a quality gate that filters out disambiguation noise.
  - *Journals* — leading venues by count of highly-cited articles (type = journal).
- **🔎 Search** — type-ahead any institution, author, or journal by name.
- **Profiles** — works, citations, h-index/i10, research areas, top works, and the
  institution's social-science output, each linking out to the source.

## Run / deploy
Just open `index.html`, or serve the folder. Designed for **GitHub Pages**
(static). Shares the Research-Suite "Throughline" design tokens + `syed-theme`.

> Working name **ScholarScope** — rename in `<title>` + the `.bar-name` mark before
> first deploy if desired.
