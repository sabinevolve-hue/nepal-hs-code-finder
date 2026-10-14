# Customs Nepal — Google Play handoff guide

How to publish Customs Nepal (www.customsnepal.com) to the Google Play Store as an Android app.
The app is a **TWA (Trusted Web Activity)** — a thin Android wrapper that opens the live website full-screen,
with no browser address bar, installable like any native app. Package: **`com.customsnepal.app`**.

Last updated: 2026-10-14.

---

## 1. Status — what is already done (in this repo, deployed)

The web side is **100% ready**. Nothing more is needed in code to ship a Play app:

- **Installable PWA** — `public/manifest.webmanifest` (name, icons, theme, shortcuts, **screenshots**), service worker `public/sw.js`, and a service-worker registration in the page.
- **App icons** — `icon-192.png`, `icon-512.png`, `icon-512-maskable.png`, `icon-180.png`.
- **Digital Asset Links file** — `public/.well-known/assetlinks.json`, already serving at `https://www.customsnepal.com/.well-known/assetlinks.json`, declaring package `com.customsnepal.app`. ⚠️ The SHA-256 fingerprint in it is a placeholder — **it must be replaced with your real signing key** (see §4, this is the one step that most often breaks TWAs).
- **Store artwork — generated and committed** in `public/`:
  - `play-feature-graphic.png` — 1024×500 feature graphic (required).
  - `screenshot-home.png`, `screenshot-track.png`, `screenshot-safta.png` — 1080×2280 phone screenshots.
  - `screenshot-home-wide.png` — 1280×800 (tablet/wide).
  - `icon-512.png` — doubles as the 512×512 Play app icon.
- **Privacy policy** — live at `https://www.customsnepal.com/privacy` (Play requires a URL).

## 2. What needs YOU (Sabin) — I cannot do these

These require a Google account, a payment, and a code-signing identity, which only you can provide:

1. **Create a Google Play Console account** — one-time **US$25** fee, plus identity + address verification. https://play.google.com/console/signup
2. **Choose account type carefully** — see the testing rule in §6. An **Organization** account (register Evolve Tech) skips the 12-tester / 14-day requirement that **Personal** accounts created recently must complete before production. For a business app, Organization is the better choice.
3. **Generate & hold the signing key** (the AAB build in §3 does this).
4. **Upload the app bundle (.aab)** and complete the store listing, data-safety and content-rating forms.
5. **Submit for review.**

I've prepared everything up to those points, including ready-to-paste listing copy (§5).

---

## 3. Build the Android app bundle (.aab) — easiest path: PWABuilder

No Android Studio needed. ~15 minutes.

1. Go to **https://www.pwabuilder.com** and enter `https://www.customsnepal.com`. It scores the PWA (should pass — manifest, service worker, icons are all present).
2. Click **Package for stores → Android**.
3. In the options dialog, confirm:
   - **Package ID:** `com.customsnepal.app` (must match `assetlinks.json` and the manifest — do not change it).
   - **App name:** `Customs Nepal`
   - **Launcher name:** `Customs Nepal`
   - **Signing key:** choose **"Create new"** (PWABuilder generates one and returns it in the zip). Keep **`signing.keystore`** and the passwords it shows you **forever** — losing them means you can never update the app.
   - Leave **"Use Play App Signing"** ticked (recommended).
4. Click **Generate**, then **Download**. The zip contains:
   - `app-release-bundle.aab` ← this is what you upload to Play.
   - `signing.keystore` + `signing-key-info.txt` (your key + passwords — back these up).
   - `assetlinks.json` ← **the correct one for your key** (see §4).

**Alternative (CLI, if you prefer):** `npx @bubblewrap/cli init --manifest https://www.customsnepal.com/manifest.webmanifest` then `bubblewrap build`. Same result.

---

## 4. ⚠️ The one step that breaks TWAs: Digital Asset Links

A TWA only runs **full-screen without a browser bar** if the website and the app verify each other. That handshake is the SHA-256 fingerprint of your **app signing key**, published at `/.well-known/assetlinks.json`.

The fingerprint currently committed in `public/.well-known/assetlinks.json` is a **placeholder** and will NOT match your key. You must replace it:

1. **If you use Play App Signing (recommended):** after your first upload to Play Console, open **Play Console → (your app) → Test and release → Setup → App signing**. Copy the **"SHA-256 certificate fingerprint"** under *App signing key certificate*.
2. Paste that fingerprint into `public/.well-known/assetlinks.json` (replace the `25:20:ED:…` value). You can add **both** the upload-key and the app-signing-key fingerprints to the array — safest.
   - Or just copy the `assetlinks.json` that PWABuilder generated — but if Play re-signs with its own key, Play Console's fingerprint (step 1) is the authoritative one.
3. Commit and push — Vercel redeploys `https://www.customsnepal.com/.well-known/assetlinks.json` in ~1 minute.
4. Verify: `https://developers.google.com/digital-asset-links/tools/generator` (Statement List Generator and Tester), or just reinstall the app — if the address bar is gone, it verified.

> Until this matches, the app still works but shows a thin Chrome URL bar at the top. Fix it before or right after launch.

---

## 5. Store listing — ready to paste

**App name** (max 30 chars): `Customs Nepal`

**Short description** (max 80 chars):
`Nepal HS codes, import duty, VAT & landed cost. Tariff 2026/27, SAFTA & trade.`

**Full description** (max 4000 chars):
```
Customs Nepal is the fastest way to find the HS code, customs duty, VAT and total landed cost for anything imported into Nepal — built on the official Customs Tariff 2026/27 (FY 2083/84).

SEARCH THE FULL TARIFF
• All 6,340 import tariff lines, searchable by product name, material, HS code, trade name — in English or Nepali (मोबाइल, चामल, सोलार).
• General vs SAARC/SAFTA duty, VAT, unit, LDC rate and export duty for every line.
• Chapter legal notes, section notes and the General Rules of Interpretation.

DUTY & LANDED-COST CALCULATOR
• Enter CIF value and get customs duty, excise, VAT (13%) and the final landed cost in rupees — including specific per-unit duties.

ASK AI
• Describe a product in plain words and get ranked HS-code suggestions with reasoning.

SAFTA PREFERENTIAL DUTY
• Learn how to pay the lower SAARC rate: eligible origins, rules of origin, certificate of origin, the sensitive list, and the product segments that benefit most.

SHIPPING TO NEPAL
• The sea–land routes for landlocked Nepal: gateway ports (Kolkata/Haldia, Visakhapatnam, Nhava Sheva, Mundra, Mongla, Chittagong) and inland customs points (Birgunj, Biratnagar, Bhairahawa, Kakarbhitta, Chobhar).
• Paste a container or bill-of-lading number to detect the carrier and jump to its live tracker.

TRADE DATA
• Multi-year Department of Customs foreign-trade statistics: products, chapters, countries, customs points, trends.

EXPORT GUIDES
• Step-by-step guides to exporting from Nepal — procedures, documents, EXIM code and certificate of origin.

Customs Nepal is a free, independent reference tool. It is not a government website; always confirm final rates with the customs office or a clearing agent before pricing a shipment.
```

**App category:** Finance (alternative: Business)
**Tags:** customs, HS code, import, tariff, Nepal, trade, SAFTA, shipping
**Contact email:** sabin.evolve@gmail.com
**Website:** https://www.customsnepal.com
**Privacy policy:** https://www.customsnepal.com/privacy

**Graphics to upload** (all in `public/`):
| Play asset | File | Size |
|---|---|---|
| App icon | `icon-512.png` | 512×512 |
| Feature graphic | `play-feature-graphic.png` | 1024×500 |
| Phone screenshots (2–8) | `screenshot-home.png`, `screenshot-track.png`, `screenshot-safta.png` | 1080×2280 |
| Tablet screenshot (optional) | `screenshot-home-wide.png` | 1280×800 |

> Download these from the repo or from the live site, e.g. `https://www.customsnepal.com/play-feature-graphic.png`.

---

## 6. Play Console forms + the testing rule

In Play Console, after creating the app, complete (Play will checklist these for you):

1. **Store listing** — paste §5; upload graphics.
2. **App content** — Privacy policy URL; **Data safety** (this app collects no personal data and has no login/account — declare "No data collected"; the AI assistant sends the typed query to the server only to answer, not stored); **Content rating** questionnaire (Everyone); **Target audience** (not directed at children); **Ads** (none); **Government app** (No — declare it's independent).
3. **Production → Create release** — upload `app-release-bundle.aab`, add release notes, roll out.

⚠️ **Closed-testing requirement (personal accounts):** Google requires **new Personal developer accounts** (created after ~Nov 2023) to run a **closed test with at least 12 testers opted in for 14 continuous days** before they can apply for production access. **Organization accounts are exempt.** If you register as **Evolve Tech (Organization)**, you can go straight to production. If you go Personal, budget ~2–3 weeks and line up 12 testers (an email list you add under Closed testing → testers).

Review itself typically takes a few hours to a few days for a first app.

---

## 7. Keeping the app updated

Because it's a TWA, **the app content is just the live website** — every deploy to `www.customsnepal.com` updates what users see **instantly**, with no Play review. You only rebuild and re-upload an `.aab` when you need to change the Android shell itself (app name, icon, target API level for Play's annual requirement, or the splash screen). Reuse the **same `signing.keystore`** from §3 every time, and bump `versionCode`/`versionName` in PWABuilder/Bubblewrap.

---

## Quick checklist

- [ ] Create Play Console account (Organization = no testing wait) — **you**, US$25
- [ ] PWABuilder → Android → download `.aab` + keystore — **you** (I can't sign)
- [ ] **Back up `signing.keystore` + passwords**
- [ ] Upload `.aab`, paste listing (§5), upload graphics (already in `public/`)
- [ ] Copy Play's app-signing SHA-256 → update `assetlinks.json` → push (§4)
- [ ] Complete Data safety / Content rating / Target audience
- [ ] (Personal account only) 12 testers × 14 days closed test
- [ ] Submit for review
