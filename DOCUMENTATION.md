# customsnepal.com — Project Documentation

Maintainer & architecture guide for the **Nepal HS Code Finder / customsnepal.com** website.
Last updated: 2026-09-30.

---

## 1. What this is

A mobile-first web app for Nepal import/export:

- **Search** the full Nepal Customs Tariff 2026/27 by HS code, product name, material or family (6,340 lines).
- **Ask AI** — describe a product in plain English/Nepali and get the likely Nepal HS code(s) with reasoning (DeepSeek).
- **Trade data** — 7–8 years of Department of Customs foreign-trade statistics: totals, chapters, products, countries (with per-country product drill-down), customs points, duty bands, monthly trends.
- **Browse** — sections, chapters, notes, rules of interpretation, export duty schedule, customs offices, About Nepal Customs.
- **Calculator** — single-product landed-cost estimate (CIF → duty → VAT → landed cost).
- **Invoice generator** — build a Proforma / Commercial Invoice + Customs & Landed Cost estimate from typed items or an **uploaded invoice** (Excel/CSV/PDF/photo) that AI reads (parties, bank, shipment, line items). Downloads a multi-sheet **master Excel** + a PDF.

### Live URLs
- Production: **https://customsnepal.com** (apex 308-redirects to https://www.customsnepal.com)
- Vercel URL: https://nepal-hs-code-finder-tzco.vercel.app
- GitHub: **https://github.com/sabinevolve-hue/nepal-hs-code-finder**

### Tech stack
- **Frontend:** one self-contained `src.html` (vanilla JS, no framework). Data is inlined at build time. Charts: Apache ECharts 5.5.1 (CDN). Excel: ExcelJS (CDN, lazy). Spreadsheet/PDF/OCR readers: SheetJS / pdf.js / Tesseract.js (CDN, lazy).
- **Backend:** one Vercel serverless function `api/classify.js` — a locked-down proxy to DeepSeek (or Anthropic) for the AI features. No database.
- **Data build:** Python scripts (`scripts/*.py`) turn the source PDF/Excel into compact JSON.
- **Hosting:** Vercel (static `public/` + the one serverless function). Auto-deploys on push to `main`.
- **Fonts:** Apple San Francisco system stack (real SF Pro on Apple devices, system fonts elsewhere — like apple.com). No web-font download.

---

## 2. Repository layout

```
nepal-hs-code-finder/
├── src.html                 # THE app — all HTML/CSS/JS. Edit this, then run the build.
├── public/
│   └── index.html           # GENERATED (src.html + inlined data + <head> + analytics). Served by Vercel. Do not hand-edit.
├── api/
│   └── classify.js          # Serverless AI proxy (DeepSeek/Anthropic), locked to Nepal-customs tasks.
├── vercel.json              # Vercel config (output dir = public).
├── package.json             # npm scripts (build:data, build, refresh, dev).
├── data/
│   ├── tariff.json          # Compact tariff (inlined as /*DATA*/). Built by build.py.
│   ├── stats.json           # Compact trade statistics (inlined as /*STATS*/). Built by stats.py.
│   ├── offices.json         # Customs offices + department info (inlined as /*OFFICES*/). Hand-maintained.
│   ├── gri.json             # General Rules of Interpretation + abbreviations text.
│   ├── parsed.json          # Intermediate parse output (parse.py → build.py).
│   ├── customs-tariff-2026-27.txt   # Source: extracted text of the tariff PDF.
│   ├── fts/<fy>/*.xlsx       # Source: Dept. of Customs FTS workbooks per fiscal year (git-ignored, large).
│   └── sources/             # Catalogue of downloaded customs.gov.np files.
└── scripts/
    ├── parse.py             # tariff PDF text  → data/parsed.json
    ├── aliases.py           # everyday/Nepali product names → HS prefixes (used by build.py)
    ├── build.py             # parsed.json (+ gri, aliases) → data/tariff.json
    ├── stats.py             # data/fts/**/*.xlsx → data/stats.json (multi-year)
    ├── assemble.py          # src.html + data JSON → public/index.html   (THE build step)
    ├── refresh.py           # crawl customs.gov.np, download new FTS files, rebuild stats + page
    ├── gen-proforma.js      # Node/ExcelJS reference generator for the invoice workbook (portable to browser)
    ├── customs-site/        # crawler used to catalogue/download customs.gov.np documents
    └── _pi_fixture.json     # a real shipment used to validate gen-proforma.js (git-ignored — business data)
```

Placeholders `assemble.py` fills in `src.html`: `/*DATA*/` (tariff), `/*STATS*/` (stats), `/*OFFICES*/` (offices).

---

## 3. Build & run

Requires Python 3 and Node ≥ 18.

```bash
# 1) (only when source data changes) rebuild the data JSON
npm run build:data          # parse.py + build.py + stats.py

# 2) assemble the page (ALWAYS run after editing src.html or the data)
npm run build               # assemble.py → public/index.html

# 3) preview locally
npm run dev                 # serves public/ at http://localhost:8080
```

**Golden rule:** never hand-edit `public/index.html`. Edit `src.html` (or the data), then run `npm run build`. Commit both `src.html` and the regenerated `public/index.html`.

---

## 4. Deployment (Vercel)

- The repo is linked to the Vercel project **`nepal-hs-code-finder-tzco`** (team `sabinevolve-hue`).
- **Push to `main` → Vercel auto-builds and deploys.** `vercel.json` sets the output directory to `public`, and `api/classify.js` is deployed as a serverless function.
- No build command runs on Vercel — the committed `public/index.html` is served as-is. So you must run `npm run build` locally and commit the result.
- To roll back: Vercel dashboard → Deployments → promote a previous deployment.

### Environment variables (Vercel → Project → Settings → Environment Variables)
| Name | Purpose |
|---|---|
| `DEEPSEEK_API_KEY` | DeepSeek API key — powers the AI (Ask AI, Suggest HS, invoice extraction). **Set.** |
| `ANTHROPIC_API_KEY` | Optional fallback provider (Claude). |
| `AI_PROVIDER` | Optional: force `deepseek` or `anthropic`. Defaults to DeepSeek if its key is present. |
| `DEEPSEEK_MODEL` / `ANTHROPIC_MODEL` | Optional model override. |

**Important:** after adding/changing an env var, **redeploy** (push any commit, or Vercel → Redeploy) — existing deployments do not pick up new env vars. Check status at `https://customsnepal.com/api/classify` (should return `{"configured":true,"provider":"deepseek","scope":"nepal-customs",...}`).

---

## 5. Domain & DNS

- Domain **customsnepal.com** registered at **Nest Nepal** (myaccount.nestwebhost.com).
- **Nameservers = Vercel:** `ns1.vercel-dns.com`, `ns2.vercel-dns.com` (set at Nest Nepal). Vercel manages DNS + issues the free SSL automatically.
- In Vercel the domain is in the `sabinevolve-hue` account and attached to the project; apex `customsnepal.com` **308-redirects to `www.customsnepal.com`**.
- Registrar lock is **ON** at Nest Nepal.
- If you ever need email or other DNS records, add them in **Vercel → Domains → customsnepal.com → DNS** (not at Nest Nepal, since Vercel is authoritative).

---

## 6. The AI (api/classify.js) — how it works & how it's secured

The browser never sends a free-form prompt. It sends `{ task, messages }`; the **server owns the prompts** and only runs three allowed tasks, all scoped to the Nepal-customs domain:

| task | used by | what it does |
|---|---|---|
| `assistant` | Ask AI tab | HS classification + Nepal customs Q&A, with two tariff tools (`search_tariff`, `lines_under_heading`), multi-round. |
| `classify` | Invoice → "Suggest HS codes" | one-shot: product list → Nepal HS codes + notes. |
| `extract` | Invoice upload | invoice text → structured {seller, buyer, bank, shipment, items}. |

Security layers (all in `api/classify.js`):
- **Task allow-list** — any other `task` → HTTP 400. The endpoint cannot be used as a general chatbot.
- **Server-owned, domain-scoped prompts** — each refuses anything not about Nepal customs.
- **Origin allow-list** — requests from other sites → HTTP 403 (`ALLOW` set).
- **Tool allow-list** — only `search_tariff` / `lines_under_heading` are relayed.
- **Caps** — per-task output-token limits + inbound size limit.

**Cost backstop:** set a monthly spending limit on the DeepSeek account (platform.deepseek.com → billing). Optional next layer: per-IP rate limiting via Vercel KV/Upstash.

To change provider or model, set the env vars above and redeploy. To broaden/narrow what the AI will answer, edit the `SCOPE` / `SYS` strings in `api/classify.js`.

---

## 7. Updating the trade statistics (new FY data)

Source: Department of Customs Foreign Trade Statistics (FTS) Excel workbooks, published at customs.gov.np. Each annual workbook has the same 10-sheet layout; `stats.py` reads them.

1. Put new workbook(s) in `data/fts/<fiscal-year>/` (e.g. `data/fts/2083-84/FTS_....xlsx`). Fiscal-year folder names look like `2082-83`.
2. Rebuild: `python3 scripts/stats.py` then `python3 scripts/assemble.py` (or `npm run build:data && npm run build`).
3. Commit `data/stats.json` and `public/index.html`, push → deploys.

`scripts/refresh.py` automates crawl+download+rebuild, but the manual path above is the reliable one. Values in the workbooks are in **Rs. thousand**; the page multiplies by 1,000 and shows **Arab / Crore** (1 Arab = 100 Crore = NPR 1 billion), with a Billion/Million toggle.

Per-country product drill-down data (`country_prod` in stats.json, latest full year, top-20 products/country/direction) is produced inside `stats.py`'s `read()`.

---

## 8. Updating the tariff (new tariff year)

1. Replace the source text `data/customs-tariff-2026-27.txt` with the new tariff's extracted text.
2. Run `python3 scripts/parse.py` (PDF text → parsed.json), then `python3 scripts/build.py` (→ tariff.json). Adjust `scripts/aliases.py` for new everyday-name → HS mappings.
3. `python3 scripts/assemble.py`, commit, push.

Known limitation: the Nepali integrated-tariff PDF uses a non-Unicode font, so per-line VAT/excise couldn't be extracted. The site uses the printed **customs duty** rate; VAT is applied at the flat 13% and excise is a user input in the calculator.

---

## 9. Customs offices / About pages

Hand-maintained in `data/offices.json` (department contact, hours, vision, NECAS text, role abbreviations, and ~40 offices with location, province, border type, phone/email, chief, and a `stat` key that links to the trade-data customs points). Edit the JSON, run `npm run build`, commit. Office heads change on transfer — re-verify periodically from customs.gov.np.

---

## 10. Analytics

Two trackers, injected by `assemble.py` **only on the live domain** (customsnepal.com / *.vercel.app) — the artifact/preview copy loads no trackers.

- **Vercel Web Analytics** — cookieless, privacy-friendly visitor & page-view counts. View: Vercel dashboard → project → **Analytics** tab.
- **Google Analytics 4** — property "Customs Nepal", Measurement ID **`G-T1FQWWL2VV`**. Deeper marketing view (real-time, acquisition, geography, devices). View: analytics.google.com → Customs Nepal.

To change the GA ID, edit `G-T1FQWWL2VV` in `scripts/assemble.py` and rebuild. The footer discloses the analytics cookies.

---

## 11. Privacy & data handling

- The site is **static** — there is **no server database**. Everything a user types stays in their **own browser**.
- The **invoice generator** keeps its draft in `sessionStorage` (cleared when the tab/browser closes), so a new visitor — or the next person on a shared computer — starts from a blank form. Any legacy `localStorage` draft is wiped on load. A "New / clear" button wipes it on demand.
- Calculator/saved-codes preferences use `localStorage` (non-sensitive).
- The only data that leaves the browser: (a) analytics pageview pings (Vercel/GA), and (b) when a user uses the AI reader or "Suggest HS codes", the **invoice/product text** is sent to the DeepSeek API to process that request (not stored by the site).

---

## 12. Front-end structure (src.html)

One file. Key anchors (search for these):
- `const D`, `const ST`, `const OF` — parsed inlined data (tariff, stats, offices).
- Tabs handled by `go(tab)`; sections are `#v-search / #v-ai / #v-stats / #v-browse / #v-calc / #v-invoice / #v-saved`.
- `renderResults()` (search), `askAI()` / `AI_RULES` / `AI_TOOLS` (Ask AI), `renderStats()` + `stView` (trade), `renderBrowse()` (browse), `calc()` (calculator).
- Invoice: `initInvoice()`, `invItems`, `renderInvRows()`, `buildInvoiceWorkbook()` (ExcelJS), `importInvoiceFile()` → `extractFileText()` + `aiExtractInvoice()` + `applyExtracted()`, `suggestHS()`, `clearInvoice()`.
- Units/format: `rs()` (Arab/Crore/Billion), `npr()`, `K = 1000` (stats are Rs. thousand).
- To add a tab: add a `<section id="v-x">`, a nav button (desktop `.nav-desk` + mobile `.tabbar`), add `'x'` to the `go()` section list + hash routing, and a render function.

### Testing
Playwright scripts were used per feature (route ECharts/ExcelJS/SheetJS from local `node_modules` copies since the build container's proxy blocks some CDNs). Real browsers on the live site load them from CDN normally.

---

## 13. Common issues / troubleshooting

- **AI says "not switched on":** `DEEPSEEK_API_KEY` missing or a redeploy hasn't happened since it was added. Check `/api/classify` GET.
- **AI returns "unsupported_task" / "forbidden_origin":** expected — the endpoint is locked; only the site's own three tasks from the site's origin work.
- **New env var not taking effect:** redeploy (Vercel only reads env vars at build/deploy time).
- **Charts blank:** ECharts CDN blocked/失败; check the `<script src=echarts>` loads. On the live site it loads from jsDelivr.
- **Trade values look wrong:** remember source is Rs. thousand → page ×1000; 1 Arab = NPR 1 billion.
- **SSL/"No SSL" warning at Nest Nepal:** ignore — SSL is issued by Vercel (nameservers point to Vercel). Never buy SSL at Nest Nepal.

---

## 14. Roadmap / possible next steps

- Per-IP rate limiting on `/api/classify` (Vercel KV/Upstash) + DeepSeek spend cap.
- Optional cookie-consent banner for international visitors.
- Accounts (save invoices/estimates) — would need a backend/auth (e.g. Supabase); currently everything is client-side.
- Packing List sheet in the invoice master file.
- Earlier trade years (2072/73–2075/76); revenue-by-office; country × product deeper drill-down.
- Deeper design pass (8-pt spacing audit, WCAG AA contrast/focus sweep).

---

*Prepared for Evolve Tech / Audio Visual Solutions Pvt. Ltd. Duty and trade data © Department of Customs, Government of Nepal.*
