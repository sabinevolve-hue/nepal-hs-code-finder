// Cloudflare Worker for world.customsnepal.com. Static files are served by Cloudflare directly and never reach this
// script; it runs only for requests no file matched: the old three-letter country addresses with a year or export
// code (regex redirects in routes.js, generated from vercel.json by scripts/cf_config.py), else 404.html.
import routes from './routes.js';
import { redirectFor, notFound } from '../../cf/lib.js';

const RX = routes.map(([p, d, c]) => [new RegExp(p), d, c]);

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    return redirectFor(RX, url) || notFound(env, url);
  },
};
