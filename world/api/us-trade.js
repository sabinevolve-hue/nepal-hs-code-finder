// Vercel serverless function for world.customsnepal.com: US trade in goods by product, from the U.S. Census Bureau.
//
// Why it exists: the Census API needs a key. The key lives ONLY in this project's environment (CENSUS_API_KEY) and is
// added to the request here, so it is never in the repository, in a browser, or in the data-refresh scripts.
// scripts/world_us_products.py reads the monthly figures through this endpoint.
//
// It is not a general proxy: the caller chooses among a few fixed values and the URL to the Census API is built here.
//   GET /api/us-trade?flow=exports|imports&time=YYYY-MM&level=HS2|HS4|HS6[&commodity=<digits>][&partners=1]
// Responses are public statistics and are cached at the edge for a day.
const VARS = {
  exports: { code: 'E_COMMODITY', month: 'ALL_VAL_MO', ytd: 'ALL_VAL_YR' },
  imports: { code: 'I_COMMODITY', month: 'GEN_VAL_MO', ytd: 'GEN_VAL_YR' },
};

module.exports = async (req, res) => {
  res.setHeader('X-Robots-Tag', 'noindex');
  if (req.method !== 'GET') { res.statusCode = 405; return res.end(JSON.stringify({ error: 'GET only' })); }
  const q = req.query || {};
  const flow = String(q.flow || ''), time = String(q.time || ''), level = String(q.level || 'HS6'), commodity = String(q.commodity || ''), partners = q.partners === '1';
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  if (!VARS[flow] || !/^20\d\d-(0[1-9]|1[0-2])$/.test(time) || !/^HS[246]$/.test(level) || !/^\d{0,6}$/.test(commodity)) {
    res.statusCode = 400; return res.end(JSON.stringify({ error: 'flow=exports|imports, time=YYYY-MM, level=HS2|HS4|HS6, commodity=digits (optional), partners=1 (optional)' }));
  }
  const key = process.env.CENSUS_API_KEY;
  if (!key) { res.statusCode = 503; return res.end(JSON.stringify({ error: 'not configured: CENSUS_API_KEY is not set for this project' })); }
  const v = VARS[flow];
  const get = [v.code, v.month, v.ytd].concat(partners ? ['CTY_CODE', 'CTY_NAME'] : []).join(',');
  const params = new URLSearchParams({ get, time, COMM_LVL: level });
  if (commodity) params.set(v.code, commodity.length < +level[2] ? commodity + '*' : commodity);
  if (!partners) params.set('CTY_CODE', '-');          // '-' is the Census code for the total of all countries
  params.set('key', key);
  try {
    const r = await fetch('https://api.census.gov/data/timeseries/intltrade/' + flow + '/hs?' + params.toString(), { headers: { Accept: 'application/json' } });
    const text = await r.text();
    if (r.status === 204) { res.statusCode = 200; res.setHeader('Cache-Control', 'public, s-maxage=3600'); return res.end(JSON.stringify({ rows: [], note: 'no data for this period yet' })); }
    if (!r.ok || text.trim()[0] !== '[') {              // an error page or message from the Census API: pass the status, never the request (it holds the key)
      res.statusCode = r.ok ? 502 : r.status; return res.end(JSON.stringify({ error: 'Census API answered ' + r.status, detail: text.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 300) }));
    }
    res.statusCode = 200; res.setHeader('Cache-Control', 'public, s-maxage=86400, stale-while-revalidate=604800');
    return res.end(JSON.stringify({ source: 'U.S. Census Bureau, USA Trade Online / International Trade API', flow, time, level, rows: JSON.parse(text) }));
  } catch (e) {
    res.statusCode = 502; return res.end(JSON.stringify({ error: 'could not reach the Census API' }));
  }
};
