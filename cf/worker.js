// Cloudflare Worker for customsnepal.com. Static files (public/) are served by Cloudflare directly and never reach
// this script (requests for static files are free and unlimited). The script runs only for requests no file matched:
//   /api/classify, /api/track  -> the same handlers Vercel ran (api/*.js), through a small Vercel-style adapter;
//   regex redirects            -> cf/routes.js (generated from vercel.json by scripts/cf_config.py);
//   /_vercel/*                 -> 204 (Vercel's analytics script does not exist here);
//   anything else              -> 404.html with status 404.
// Secrets (DEEPSEEK_API_KEY, ANTHROPIC_API_KEY, MAERSK_CONSUMER_KEY, …) are Worker secrets in the Cloudflare
// dashboard; with nodejs_compat they appear in process.env exactly as on Vercel. See DOCUMENTATION.md.
import routes from './routes.js';
import classify from '../api/classify.js';
import track from '../api/track.js';
import { redirectFor, runVercel, notFound } from './lib.js';

const API = { '/api/classify': classify, '/api/track': track };
const RX = routes.map(([p, d, c]) => [new RegExp(p), d, c]);

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const p = url.pathname.replace(/\/+$/, '') || '/';
    if (API[p]) return runVercel(API[p], request);
    if (p.startsWith('/_vercel/')) return new Response(null, { status: 204 });
    return redirectFor(RX, url) || notFound(env, url);
  },
};
