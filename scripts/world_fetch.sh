#!/usr/bin/env bash
# Refresh data for world.customsnepal.com (Pillar 1 HS tree + Pillar 2 trade).
# Usage: scripts/world_fetch.sh   (run from repo root; writes world/data/*.json)
# Re-run yearly when World Bank / WITS publish a newer year, or when the HS edition changes (HS 2028 -> Jan 2028).
set -euo pipefail
RAW="$(mktemp -d)"
echo "raw dir: $RAW"

# Pillar 1 — canonical HS 6-digit tree (sections/chapters/headings/subheadings)
curl -sS --max-time 40 -o "$RAW/hs.csv" \
  "https://raw.githubusercontent.com/datasets/harmonized-system/master/data/harmonized-system.csv"

# World Bank country list (used to filter region aggregates out of partner lists)
curl -sS --max-time 40 -o "$RAW/countrylist.json" \
  "https://api.worldbank.org/v2/country?format=json&per_page=400"

# Pillar 2 — per economy: WB merchandise totals + WITS partners + WITS product mix.
# name|wbcode|witscode|partnerYear   (Russia stopped reporting to Comtrade after 2021)
for P in "USA|USA|2022" "CHN|CHN|2022" "JPN|JPN|2022" "IND|IND|2022" "RUS|RUS|2021" "EUU|EUN|2022"; do
  WB="${P%%|*}"; REST="${P#*|}"; WT="${REST%%|*}"; Y="${REST##*|}"
  curl -sS --max-time 60 -o "$RAW/wb_exp_$WB.json" "https://api.worldbank.org/v2/country/$WB/indicator/TX.VAL.MRCH.CD.WT?format=json&date=2010:2023&per_page=60"
  curl -sS --max-time 60 -o "$RAW/wb_imp_$WB.json" "https://api.worldbank.org/v2/country/$WB/indicator/TM.VAL.MRCH.CD.WT?format=json&date=2010:2023&per_page=60"
  B="https://wits.worldbank.org/API/V1/SDMX/V21/datasource/tradestats-trade/reporter/$WT/year/$Y"
  curl -sS --max-time 90 -o "$RAW/wits_expP_${WT}_$Y.xml" "$B/partner/all/product/Total/indicator/XPRT-TRD-VL"
  curl -sS --max-time 90 -o "$RAW/wits_impP_${WT}_$Y.xml" "$B/partner/all/product/Total/indicator/MPRT-TRD-VL"
  curl -sS --max-time 90 -o "$RAW/wits_expProd_${WT}.xml" "$B/partner/wld/product/all/indicator/XPRT-TRD-VL"
  curl -sS --max-time 90 -o "$RAW/wits_impProd_${WT}.xml" "$B/partner/wld/product/all/indicator/MPRT-TRD-VL"
done

python3 -I scripts/world_data.py "$RAW/hs.csv" "$RAW" data/tariff.json world/data
echo "done. Regenerate sitemap if chapters changed."
