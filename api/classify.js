// Vercel serverless function: thin proxy to the Anthropic Messages API for the in-page HS classification assistant.
// Set ANTHROPIC_API_KEY (and optionally ANTHROPIC_MODEL) in the Vercel project settings. The API key never reaches the browser.
const MODEL = process.env.ANTHROPIC_MODEL || 'claude-sonnet-4-5';
const MAX_BODY = 200 * 1024;

module.exports = async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  const key = process.env.ANTHROPIC_API_KEY;
  if (req.method === 'GET') return res.status(200).json({ configured: !!key, model: key ? MODEL : null });
  if (req.method !== 'POST') return res.status(405).json({ error: 'method_not_allowed' });
  if (!key) return res.status(503).json({ error: 'not_configured' });

  let body = req.body;
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch (e) { body = null; } }
  if (!body || !Array.isArray(body.messages) || body.messages.length === 0) return res.status(400).json({ error: 'bad_request' });
  if (JSON.stringify(body).length > MAX_BODY) return res.status(413).json({ error: 'too_large' });

  const payload = {
    model: MODEL,
    max_tokens: 2500,
    system: String(body.system || '').slice(0, 20000),
    messages: body.messages.slice(-24),
    tools: Array.isArray(body.tools) ? body.tools.slice(0, 8) : undefined,
  };
  try {
    const r = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'x-api-key': key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const text = await r.text();
    res.status(r.status).setHeader('content-type', 'application/json');
    return res.send(text);
  } catch (e) {
    return res.status(502).json({ error: 'upstream_error', message: String(e && e.message || e) });
  }
};
