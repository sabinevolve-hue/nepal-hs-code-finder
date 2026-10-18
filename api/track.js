// Vercel serverless — live shipment status for customsnepal.com's on-page tracker.
// Progressive enhancement over the existing "route out to the carrier" tracker: the browser calls
// GET /api/track?n=<container|bl>&carrier=<slug>; if the carrier is integrated AND a server-side API
// key is configured, this returns a normalized milestone timeline that the page draws itself.
// If NOT configured (no key yet, or carrier not integrated), it returns {configured:false} and the
// page keeps its current behaviour (link to the carrier's own tracker). Nothing breaks without a key.
//
// Keys stay server-side only (Vercel env vars) — never in the browser, never in the repo:
//   MAERSK_CONSUMER_KEY   — the Consumer-Key from your Maersk developer app (required for Maersk)
//   MAERSK_TRACK_URL      — optional: exact events endpoint shown on your Maersk app page
//                           (default below); override here instead of editing code.
//   MAERSK_AUTH_HEADER    — optional: the header name Maersk expects (default "Consumer-Key").
//
// Only our own origins may call it (same lock as classify.js).

const ALLOW = new Set(['customsnepal.com', 'www.customsnepal.com', 'nepal-hs-code-finder-tzco.vercel.app']);

function originOK(req) {
  const o = req.headers.origin || req.headers.referer || '';
  if (!o) return true; // same-origin navigations may omit it
  try { return ALLOW.has(new URL(o).hostname); } catch (e) { return false; }
}

// --- carrier detection (mirror of the client PFX/BLPFX, integrated carriers flagged) ---
const PFX = { MAEU:'maersk',MRKU:'maersk',MSKU:'maersk',MRSU:'maersk',MVIU:'maersk',MNBU:'maersk',MWCU:'maersk',
  MSCU:'msc',MEDU:'msc', CMAU:'cmacgm',CGMU:'cmacgm',CMCU:'cmacgm',ECMU:'cmacgm',APLU:'cmacgm',APHU:'cmacgm',
  HLCU:'hapag',HLXU:'hapag',HPLU:'hapag',HASU:'hapag', ONEU:'one',ONUU:'one',
  COSU:'cosco',CBHU:'cosco',CCLU:'cosco',CSLU:'cosco',CSNU:'cosco',CXDU:'cosco', OOLU:'oocl',OOCU:'oocl',
  SEGU:'sealand',SEKU:'sealand',SEAU:'sealand' };
const BLPFX = { ONEY:'one',MEDU:'msc',MSCU:'msc',MAEU:'maersk',MRKU:'maersk',HLCU:'hapag',COSU:'cosco',
  CMDU:'cmacgm',CMAU:'cmacgm',APLU:'cmacgm',SEAU:'sealand' };
// which slugs this endpoint can actually fetch live (others -> route out on the page)
const INTEGRATED = { maersk: !!process.env.MAERSK_CONSUMER_KEY };

function detectCarrier(n) {
  const cn = String(n || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
  const p4 = cn.slice(0, 4);
  if (/^[A-Z]{4}[0-9]{7}$/.test(cn)) return { cn, carrier: PFX[p4] || null, kind: 'container' };
  if (/^[A-Z]{4}/.test(cn) && cn.length >= 9) return { cn, carrier: BLPFX[p4] || PFX[p4] || null, kind: 'bl' };
  return { cn, carrier: null, kind: null };
}

// --- DCSA-style event normalizer (Maersk Track & Trace follows the DCSA T&T standard) ---
const EQ = { LOAD:'Loaded on vessel', DISC:'Discharged from vessel', GTIN:'Gated in at terminal',
  GTOT:'Gated out of terminal', STUF:'Container stuffed', STRP:'Container stripped', PICK:'Picked up', DROP:'Returned empty', INSP:'Inspected', RSEA:'Resealed' };
const TR = { ARRI:'Arrived', DEPA:'Departed' };
const SH = { RECE:'Received', DRFT:'Draft', PENA:'Pending', CONF:'Confirmed', ISSU:'Issued', SURR:'Surrendered', CMPL:'Completed', HOLD:'On hold', RELS:'Released' };

function locName(ev) {
  const loc = (ev.transportCall && ev.transportCall.location) || ev.location || ev.eventLocation || {};
  return loc.locationName || loc.name || loc.UNLocationCode || loc.unLocationCode || '';
}
function milestone(ev) {
  const t = ev.equipmentEventTypeCode || ev.transportEventTypeCode || ev.shipmentEventTypeCode;
  const m = EQ[t] || TR[t] || SH[t];
  if (m) return m;
  if (ev.description) return String(ev.description);
  return (ev.eventType ? ev.eventType.toLowerCase() : 'Status') + ' update';
}
function normalize(data) {
  let list = [];
  if (Array.isArray(data)) list = data;
  else if (data && Array.isArray(data.events)) list = data.events;
  else if (data && Array.isArray(data.shipmentEvents)) list = data.shipmentEvents;
  else if (data) list = [].concat(data.transportEvents || [], data.equipmentEvents || [], data.shipmentEvents || []);
  const out = list.map(ev => {
    const cls = (ev.eventClassifierCode || ev.eventClassifier || 'ACT').toUpperCase();
    return {
      milestone: milestone(ev),
      location: locName(ev),
      time: ev.eventDateTime || ev.eventDateTimeUTC || ev.dateTime || ev.eventCreatedDateTime || null,
      planned: cls === 'EST' || cls === 'PLN'
    };
  }).filter(e => e.time || e.location);
  out.sort((a, b) => new Date(a.time || 0) - new Date(b.time || 0));
  return out;
}

async function fetchMaersk(info) {
  const key = process.env.MAERSK_CONSUMER_KEY;
  if (!key) return { configured: false };
  const base = process.env.MAERSK_TRACK_URL || 'https://api.maersk.com/track-and-trace-private/events';
  const header = process.env.MAERSK_AUTH_HEADER || 'Consumer-Key';
  const param = info.kind === 'container' ? 'equipmentReference' : 'transportDocumentReference';
  const url = base + (base.indexOf('?') >= 0 ? '&' : '?') + param + '=' + encodeURIComponent(info.cn);
  const headers = { Accept: 'application/json' }; headers[header] = key;
  const ctl = new AbortController(); const timer = setTimeout(() => ctl.abort(), 9000);
  try {
    const r = await fetch(url, { headers, signal: ctl.signal });
    if (!r.ok) return { configured: true, ok: false, status: r.status };
    const data = await r.json();
    return { configured: true, ok: true, events: normalize(data) };
  } catch (e) {
    return { configured: true, ok: false, error: 'upstream_unreachable' };
  } finally { clearTimeout(timer); }
}

module.exports = async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  if (!originOK(req)) return res.status(403).json({ error: 'forbidden_origin' });

  const n = (req.query && req.query.n) || '';
  // probe: GET /api/track with no number -> what's live
  if (!n) return res.status(200).json({ ok: true, integrated: INTEGRATED });

  const info = detectCarrier(n);
  const hinted = (req.query && req.query.carrier) || info.carrier;
  const carrier = info.carrier || hinted || null;
  if (!carrier) return res.status(200).json({ ok: true, carrier: null, configured: false, events: [] });
  if (carrier !== 'maersk' || !INTEGRATED.maersk) {
    // carrier not integrated yet (or no key) -> page keeps the route-out link
    return res.status(200).json({ ok: true, carrier, configured: false, events: [] });
  }

  const r = await fetchMaersk(info);
  const events = (r.ok && r.events) || [];
  // cache successful, non-empty results at the edge for 6h; empty/errors briefly
  res.setHeader('Cache-Control', events.length ? 'public, s-maxage=21600, stale-while-revalidate=86400' : 'public, s-maxage=120');
  return res.status(200).json({ ok: !!r.ok, carrier, configured: !!r.configured, events, kind: info.kind });
};
