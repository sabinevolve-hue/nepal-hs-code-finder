// Cloudflare Worker for world.customsnepal.com. Static files are served by Cloudflare directly and never reach this
// script; it runs only for requests no file matched:
//   /api/us-trade  -> the same handler Vercel ran (world/api/us-trade.js, copied from world-src/api by
//                     world_prerender.py), through the Vercel-style adapter in cf/lib.js. It needs the Worker secret
//                     CENSUS_API_KEY (Cloudflare dashboard -> customsnepal-world -> Settings -> Variables and Secrets);
//                     with nodejs_compat it appears in process.env exactly as on Vercel;
//   regex redirects -> the old three-letter country addresses with a year or export code (routes.js, generated from
//                     vercel.json by scripts/cf_config.py);
//   anything else  -> 404.html with status 404.
import routes from './routes.js';
import usTrade from '../api/us-trade.js';
import { redirectFor, runVercel, notFound } from '../../cf/lib.js';

const API = { '/api/us-trade': usTrade };
const RX = routes.map(([p, d, c]) => [new RegExp(p), d, c]);

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const p = url.pathname.replace(/\/+$/, '') || '/';
    if (API[p]) {
      const r = await runVercel(API[p], request);
      r.headers.set('X-Robots-Tag', 'noindex');
      return r;
    }
    return redirectFor(RX, url) || notFound(env, url);
  },
};
