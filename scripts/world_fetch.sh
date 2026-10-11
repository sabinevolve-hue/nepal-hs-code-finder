#!/usr/bin/env bash
# Refresh data for world.customsnepal.com.
#   Pillar 1 (HS tree)      -> world/data/hs.json      via world_data.py
#   Pillar 2 (global trade) -> world/data/trade.json   via world_trade.py
# Usage: scripts/world_fetch.sh   (run from repo root)
# Re-run yearly when World Bank / WITS publish a newer year, or for a new HS edition (HS 2028 -> Jan 2028).
set -euo pipefail
RAW="$(mktemp -d)"; echo "raw dir: $RAW"
WB="https://api.worldbank.org/v2"
WITS="https://wits.worldbank.org/API/V1/SDMX/V21/datasource/tradestats-trade/reporter"

# Pillar 1 — canonical HS 6-digit tree + WB country list (names/regions, aggregate filter)
curl -sS --max-time 40 -o "$RAW/hs.csv" "https://raw.githubusercontent.com/datasets/harmonized-system/master/data/harmonized-system.csv"
curl -sS --max-time 40 -o "$RAW/countrylist.json" "$WB/country?format=json&per_page=400"

# Pillar 2 — all-country merchandise totals (every economy's totals/trend/rank + WLD world totals)
curl -sS --max-time 90 -o "$RAW/wb_all_exp.json" "$WB/country/all/indicator/TX.VAL.MRCH.CD.WT?format=json&date=2010:2023&per_page=20000"
curl -sS --max-time 90 -o "$RAW/wb_all_imp.json" "$WB/country/all/indicator/TM.VAL.MRCH.CD.WT?format=json&date=2010:2023&per_page=20000"

# Deep partner/product detail (WITS, from UN Comtrade) for the largest traders + Nepal; latest-year fallback.
DEEP="CHN USA DEU NLD JPN ITA FRA KOR MEX BEL HKG ARE CAN GBR SGP IND RUS ESP CHE POL AUS VNM BRA SAU MYS THA IDN TUR CZE AUT NPL"
pull(){ for Y in 2022 2021 2020; do
    sz=$(curl -sS --max-time 45 "$WITS/$1/year/$Y/$3" -o "$RAW/wits_$2_$1.xml" -w "%{size_download}" 2>/dev/null)
    [ "${sz:-0}" -gt 1500 ] && { echo "$1 $2 $Y"; return; }; done; echo "$1 $2 NONE"; }
for ISO in $DEEP; do
  pull "$ISO" expP    "partner/all/product/Total/indicator/XPRT-TRD-VL"
  pull "$ISO" impP    "partner/all/product/Total/indicator/MPRT-TRD-VL"
  pull "$ISO" expProd "partner/wld/product/all/indicator/XPRT-TRD-VL"
  pull "$ISO" impProd "partner/wld/product/all/indicator/MPRT-TRD-VL"
done

python3 -I scripts/world_data.py  "$RAW/hs.csv" "$RAW" data/tariff.json world/data   # -> hs.json (also writes a trade.json, overwritten next)
python3 -I scripts/world_trade.py "$RAW" world/data                                   # -> trade.json (v2: world overview + all economies)

# Per-HS6 global top exporters/importers from BACI (CEPII — reconciled Comtrade, HS-6 bilateral).
# ~287 MB zip (HS22 = 2022–2024). Bump the version when CEPII releases a newer one.
BV="202601"; BZ="$RAW/baci_hs22.zip"
curl -sS --max-time 600 "https://www.cepii.fr/DATA_DOWNLOAD/baci/data/BACI_HS22_V${BV}.zip" -o "$BZ"
unzip -o -q "$BZ" "BACI_HS22_Y2024_V${BV}.csv" "country_codes_V${BV}.csv" -d "$RAW"
python3 -I scripts/world_products.py "$RAW/BACI_HS22_Y2024_V${BV}.csv" "$RAW/country_codes_V${BV}.csv" world/data/prod.json world/data/nepal.json  # -> prod.json + nepal.json

echo "done. If chapters or the country set changed, regenerate world/sitemap.xml."
