# Customs Nepal

**Live:** https://www.customsnepal.com · **Source:** https://github.com/sabinevolve-hue/nepal-hs-code-finder

> Brand: the site is "Customs Nepal" (customsnepal.com). "Nepal HS Code Finder" remains the descriptive
> alternate name / the HS-search feature. The repository keeps its original name for continuity.

Mobile-first search of the **Nepal Customs Tariff 2026/27** (FY 2083/84): all 6,340 import tariff lines with
general and SAARC duty rates, the export duty schedule, chapter legal notes, an import-tax / landed-cost calculator,
and an AI assistant that classifies a plain-language product description into likely HS codes. It also carries
SAFTA preferential-duty guidance, export guides, a landlocked-Nepal shipping/route layer with a container &
bill-of-lading tracker, and multi-year trade data.

A self-contained SPA (`public/index.html`) plus a set of static, server-rendered SEO landing pages
(`/tariff`, `/calculator`, `/imports`, `/exports`, `/export`, `/safta`, `/shipping`, `/shipping/track`,
`/world`, `/faq`, `/about`), built by Python scripts. Apache ECharts loads from jsDelivr. Ships as an
installable PWA (manifest + service worker) and is TWA-ready for Google Play.

## Features

- **Search by anything**: HS code in any format (`85`, `85.28`, `8528.52.10`), product name, material, function,
  everyday trade names and common Nepali words (मोबाइल, चामल, सोलार). Autocomplete suggestions and "usually found under" hints.
- **Origin switch**: General rate (China and others) vs SAARC rate (India, Bangladesh, etc.).
- **Filters**: duty band (free / up to 10 / up to 20 / over 20 %) and chapter.
- **Code detail**: both duty rates, VAT, unit, LDC rate, export duty, full section → chapter → heading → line path,
  every sibling line under the same heading, chapter legal notes and the source page number in the PDF.
- **Browse**: 21 sections → 97 chapters → headings → lines, with a filter box at every level; section and chapter
  legal notes, the General Rules of Interpretation, abbreviations, and the export duty schedule.
- **Calculator**: CIF value, customs duty, excise, VAT 13 %, other costs → landed cost and cost per unit,
  including specific per-unit duties (e.g. "Rs. 300 per litre or 80 %, whichever is higher").
- **Ask AI**: describe the product (English or Nepali, optional photo when supported); the assistant searches the
  tariff with tools, returns ranked candidates with reasons and confidence, and asks clarifying questions.
- **Trade data**: Department of Customs foreign trade statistics — latest full year (FY 2082/83) in detail, seven
  years of history (FY 2076/77 →), monthly series for the last three years, and the current year to date. A fiscal-year
  selector switches every view; Compare puts any two years side by side and tracks any product, chapter or country
  across all years. Views: Overview, Compare, Trends, Products, Chapters, Countries, Flows (sankey), Customs points, Duty bands, with per-product import/export
  figures, source countries and a seven-year sparkline inside every code's detail view. Charts by Apache ECharts.
- **SAFTA** (`/safta`): how to pay the lower SAARC duty — eligible origins, rules of origin (CTH + 40 % value add, 30 % for LDCs), certificate of origin, the sensitive list, the product segments that benefit most, and the top duty-saving products.
- **Export guides** (`/export`): exporting from Nepal — procedures, documents, EXIM code, certificate of origin, and per-product notes.
- **Shipping to Nepal** (`/shipping`): the sea–land routes for landlocked Nepal — gateway ports (Kolkata/Haldia, Visakhapatnam, Nhava Sheva, Mundra, Mongla, Chittagong) and inland customs points (Birgunj, Biratnagar, Bhairahawa, Kakarbhitta, Chobhar), each on its own page.
- **Tracker** (`/shipping/track`): paste a container or bill-of-lading number; client-side ISO 6346 check-digit validation + owner/B/L-prefix match identifies the carrier and links to its tracking page.
- **PWA / mobile app**: installable (manifest + service worker + icons) and TWA-ready for Google Play (`com.customsnepal.app`, Digital Asset Links at `/.well-known/assetlinks.json`). See `PLAYSTORE.md`.
- **Saved codes**, copy code, share link (`#hs-8528.59.00`), light/dark theme, keyboard and screen-reader friendly.

## Repository layout

```
public/index.html      built page (deployed as-is)
src.html               page source with a /*DATA*/ placeholder
data/
  customs-tariff-2026-27.txt   text layer extracted from the official PDF
  parsed.json                  structured parse (rows, headings, chapters, notes, export)
  tariff.json                  compact dataset inlined into the page
  nepal-customs-tariff-2026-27.csv   flat CSV of every line (for Excel / other tools)
  fts/<fy>/*.xlsx              Department of Customs FTS workbooks by fiscal year (not in git; see data/sources)
  stats.json                   compact multi-year trade statistics inlined into the page
  offices.json                 40 customs offices + department info (English), inlined into the page
scripts/
  parse.py          PDF text → parsed.json (handles the PDF's scrambled table columns)
  aliases.py        everyday names → HS prefixes used by search hints
  build.py          parsed.json → tariff.json
  stats.py          data/fts/**/*.xlsx → stats.json (latest year detail + history + monthly)
  assemble.py       src.html + tariff.json → public/index.html (+ robots.txt, llms.txt, sitemap.xml)
  seo_pages.py      static SEO landing pages (/tariff, /calculator, /faq, /about, …)
  export_pages.py   /exports hub + per-product export guides (/export/…)
  shipping_pages.py /shipping hub + gateway/ICD node pages + /shipping/track tracker
  safta_page.py     /safta preferential-duty page (segments, rules of origin, how to claim)
  mount_world.py    mounts the /world BACI world-trade benchmark build
api/classify.js        Vercel serverless proxy to the Anthropic API for the assistant
```

All static-page generators share one `page_head()` pattern: canonical to `https://www.customsnepal.com`,
GA4, shared `/seo.css`, a common NAV, the "Customs Nepal" header logo, and per-page JSON-LD
(BreadcrumbList / FAQPage / HowTo / Place).

## Run locally

```
npm run build                    # full chain: assemble → seo_pages → export_pages → shipping_pages → safta_page → mount_world
python3 scripts/assemble.py      # just rebuild public/index.html after editing src.html
npm run dev                      # http://localhost:8080
```

To rebuild the data from the PDF text: `npm run build:data` then `npm run build`.

## Deploy on Vercel

1. Import this repository in Vercel (framework preset: **Other**, output directory: `public`).
2. Add environment variables in the project settings (one provider is enough):
   - `DEEPSEEK_API_KEY` – DeepSeek (`deepseek-chat`, OpenAI-compatible, low cost). Optional `DEEPSEEK_MODEL`.
   - `ANTHROPIC_API_KEY` – Anthropic Claude. Optional `ANTHROPIC_MODEL` (default `claude-sonnet-4-5`).
   - `AI_PROVIDER=deepseek|anthropic` – optional, forces one when both keys are set (DeepSeek wins by default).
3. Deploy. The page works without the key; only the assistant is disabled.

Inside claude.ai the same page uses the viewer's own Claude account instead of the API key.

## Monthly refresh of trade statistics

`python3 scripts/refresh.py` crawls the Department of Customs statistics pages, downloads any new monthly or
annual workbook into `data/fts/<fy>/`, rebuilds `data/stats.json` and `public/index.html`. Commit and push to deploy.

## Updating for a new fiscal year

1. Extract the text layer of the new Customs Tariff PDF (e.g. `pdftotext -layout`) to `data/customs-tariff-2026-27.txt`
   (rename accordingly and update the version string in `scripts/build.py`).
2. Run `npm run build:data` and check the parse report (it lists any rows missing a rate).
3. Run `npm run build` and commit `public/index.html`.

## Disclaimer

Search aid and estimate only. Duty rates are transcribed from the Department of Customs' published tariff; VAT and
excise per line are not included (VAT is assumed at 13 %). The final HS classification and tax are decided by the
customs office. Confirm before pricing a shipment.

Data source: Government of Nepal, Ministry of Finance, Department of Customs — Customs Tariff 2026/2027.
