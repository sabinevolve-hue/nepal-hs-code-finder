// Shared helpers for the Cloudflare Workers of customsnepal.com and world.customsnepal.com.

// First regex redirect that matches the path; destination placeholders (:name) take the named groups.
export function redirectFor(rx, url) {
  for (const [re, dest, code] of rx) {
    const m = url.pathname.match(re);
    if (!m) continue;
    const to = dest.replace(/:([A-Za-z_]\w*)/g, (s, n) => (m.groups && n in m.groups ? m.groups[n] : s));
    return new Response(null, { status: code, headers: { Location: new URL(to + url.search, url).toString() } });
  }
  return null;
}

// The site's own 404 page, with status 404.
export async function notFound(env, url) {
  const r = await env.ASSETS.fetch(new URL('/404.html', url));
  return new Response(r.body, { status: 404, headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'public, max-age=0, must-revalidate' } });
}

// Runs a Vercel Node handler (req, res) and returns a fetch Response. Covers what api/*.js use: method, headers
// (lower-case), query, parsed JSON body, res.status/setHeader/getHeader/json/send/end.
export async function runVercel(handler, request) {
  const url = new URL(request.url);
  const headers = {};
  request.headers.forEach((v, k) => { headers[k] = v; });
  headers['x-forwarded-for'] = request.headers.get('cf-connecting-ip') || headers['x-forwarded-for'] || '';
  let body;
  if (request.method === 'POST') {
    const raw = await request.text();
    if (/application\/json/i.test(headers['content-type'] || '')) { try { body = JSON.parse(raw); } catch (e) { body = raw; } }
    else body = raw;
  }
  const req = { method: request.method, headers, query: Object.fromEntries(url.searchParams), body, url: url.pathname + url.search };
  let status = 200, payload = null;
  const out = new Headers();
  const res = {
    status(c) { status = c; return res; },
    setHeader(k, v) { out.set(k, String(v)); return res; },
    getHeader(k) { return out.get(k); },
    json(o) { if (!out.has('content-type')) out.set('content-type', 'application/json; charset=utf-8'); payload = JSON.stringify(o); return res; },
    send(b) { payload = typeof b === 'string' || b instanceof Uint8Array ? b : JSON.stringify(b); return res; },
    end(b) { if (b !== undefined) payload = b; return res; },
  };
  try {
    await handler(req, res);
  } catch (e) {
    return new Response(JSON.stringify({ error: 'server_error' }), { status: 500, headers: { 'content-type': 'application/json' } });
  }
  // Vercel's s-maxage means "CDN only"; keep it for Cloudflare's cache and out of browsers, as on Vercel
  const cc = out.get('cache-control');
  if (cc && /s-maxage/.test(cc)) { out.set('CDN-Cache-Control', cc.replace(/(^|,\s*)public,?\s*/, '').replace('s-maxage', 'max-age')); out.set('cache-control', 'public, max-age=0, must-revalidate'); }
  return new Response(payload, { status, headers: out });
}
