# ScholarScope

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
