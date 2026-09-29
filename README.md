# Nepal HS Code Finder

Mobile-first search of the **Nepal Customs Tariff 2026/27** (FY 2083/84): all 6,340 import tariff lines with
general and SAARC duty rates, the export duty schedule, chapter legal notes, an import-tax / landed-cost calculator,
and an AI assistant that classifies a plain-language product description into likely HS codes.

Single self-contained page (`public/index.html`, ~1 MB, ~200 KB gzipped). No framework, no build step beyond a Python script.

## Features

- **Search by anything**: HS code in any format (`85`, `85.28`, `8528.52.10`), product name, material, function,
  everyday trade names and common Nepali words (मोबाइल, चामल, सोलार). Autocomplete suggestions and "usually found under" hints.
- **Origin switch**: General rate (China and others) vs SAARC rate (India, Bangladesh, etc.).
- **Filters**: duty band (free / up to 10 / up to 20 / over 20 %) and chapter.
- **Code detail**: both duty rates, VAT, unit, LDC rate, export duty, full section → chapter → heading → line path,
  every sibling line under the same heading, chapter legal notes and the source page number in the PDF.
- **Browse**: 21 sections → 97 chapters → headings → lines, with a filter box at every level.
- **Calculator**: CIF value, customs duty, excise, VAT 13 %, other costs → landed cost and cost per unit,
  including specific per-unit duties (e.g. "Rs. 300 per litre or 80 %, whichever is higher").
- **Ask AI**: describe the product (English or Nepali, optional photo when supported); the assistant searches the
  tariff with tools, returns ranked candidates with reasons and confidence, and asks clarifying questions.
- **Trade data**: FY 2081/82 foreign trade statistics from the Department of Customs — imports, exports, deficit,
  top chapters, partner countries, customs points, duty-rate bands, and per-product import/export figures with
  top source/destination countries (also shown inside every code's detail view).
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
  FTS_Annual_2081_82.xlsx      Department of Customs annual foreign trade statistics (source)
  stats.json                   compact trade statistics inlined into the page
scripts/
  parse.py     PDF text → parsed.json (handles the PDF's scrambled table columns)
  aliases.py   everyday names → HS prefixes used by search hints
  build.py     parsed.json → tariff.json
  stats.py     FTS_Annual_*.xlsx → stats.json
  assemble.py  src.html + tariff.json → public/index.html
api/classify.js        Vercel serverless proxy to the Anthropic API for the assistant
```

## Run locally

```
python3 scripts/assemble.py      # rebuild public/index.html after editing src.html
npm run dev                      # http://localhost:8080
```

To rebuild the data from the PDF text: `npm run build:data` then `npm run build`.

## Deploy on Vercel

1. Import this repository in Vercel (framework preset: **Other**, output directory: `public`).
2. Add environment variables in the project settings:
   - `ANTHROPIC_API_KEY` – required for the "Ask AI" tab.
   - `ANTHROPIC_MODEL` – optional, defaults to `claude-sonnet-4-5`.
3. Deploy. The page works without the key; only the assistant is disabled.

Inside claude.ai the same page uses the viewer's own Claude account instead of the API key.

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
