# Department of Customs source files

`customs_files.csv` / `.json` — catalogue of every downloadable statistics and tariff file published on
customs.gov.np (crawled from the site's public category pages with `scripts/customs-site/crawl.py`;
`dl.py` downloads them into `files/<category>/`). 192 files:

| Category | What | Years |
|---|---|---|
| `fts-2064-065` … `fts-2070-071` | Foreign trade statistics, PDF only | FY 2064/65–2070/71 |
| `fts-2071-072` | Annual xlsx + PDF (2 parts) | FY 2071/72 |
| `fts-2072-073` … `fts-2081-082` | Annual xlsx (+ PDF book some years) and 11 monthly cumulative xlsx | FY 2072/73–2081/82 |
| `a-v-2042-063` (sic) | Monthly cumulative xlsx up to Asar = full year | FY 2082/83 |
| `foreign-trade-statistics2083-084-` | Monthly cumulative xlsx (Shrawan, Bhadra so far) | FY 2083/84 |
| `summary-of-business-revenue-*` | Monthly customs revenue summaries xlsx | FY 2071/72–2083/84 |
| `customs-tariff-rates` | Customs Tariff PDFs (English/Nepali) | 2070/71–2026/27 |
| `unified-tariff-rates` | Integrated customs tariff PDFs (Nepali, with VAT/excise columns) | 2070/71–2082/83 |
| `fts-2076-077` | Also: vehicle import data FY 2076/77 |

Sheet layout of the FTS workbooks is identical from FY 2076/77 onward (`0_Index`, `1_Trade_Direction`,
`2_Trade_Balance_Chapter`, `3_Trade_Balance_Country`, `4_Imports_By_Commodity_Partner`, `5_Imports_By_Commodity`,
`6_Exports_By_Commodity_Partner`, `7_Exports_By_Commodity`, `8_ID_Value_Comaparison`, `9_Customswise_Trade`), so
`scripts/stats.py` can process any of them. FY 2075/76 has a simpler 8-sheet layout; FY 2072/73–2074/75 use the
older "Table 1…9" layout. The files themselves (≈560 MB) are kept out of git.
