// Vercel serverless function: proxy for the in-page HS classification assistant.
// Providers (checked in this order): DEEPSEEK_API_KEY -> DeepSeek (OpenAI-compatible, tool calling),
//                                    ANTHROPIC_API_KEY -> Anthropic Messages API.
// The page always speaks the Anthropic message shape; DeepSeek traffic is translated here.
// Keys never reach the browser. Set AI_PROVIDER=anthropic|deepseek to force one.
const MAX_BODY = 200 * 1024;
const DS_MODEL = process.env.DEEPSEEK_MODEL || 'deepseek-chat';
const AN_MODEL = process.env.ANTHROPIC_MODEL || 'claude-sonnet-4-5';

function provider() {
  const p = (process.env.AI_PROVIDER || '').toLowerCase();
  if (p === 'deepseek' && process.env.DEEPSEEK_API_KEY) return 'deepseek';
  if (p === 'anthropic' && process.env.ANTHROPIC_API_KEY) return 'anthropic';
  if (process.env.DEEPSEEK_API_KEY) return 'deepseek';
  if (process.env.ANTHROPIC_API_KEY) return 'anthropic';
  return null;
}

// Anthropic-shaped messages -> OpenAI/DeepSeek chat messages
function toOpenAI(system, messages) {
  const out = [{ role: 'system', content: system }];
  for (const m of messages) {
    if (typeof m.content === 'string') { out.push({ role: m.role, content: m.content }); continue; }
    if (m.role === 'assistant') {
      const text = m.content.filter(b => b.type === 'text').map(b => b.text).join('\n');
      const calls = m.content.filter(b => b.type === 'tool_use').map(b => ({ id: b.id, type: 'function', function: { name: b.name, arguments: JSON.stringify(b.input || {}) } }));
      out.push(calls.length ? { role: 'assistant', content: text || null, tool_calls: calls } : { role: 'assistant', content: text });
    } else {
      for (const b of m.content) {
        if (b.type === 'tool_result') out.push({ role: 'tool', tool_call_id: b.tool_use_id, content: typeof b.content === 'string' ? b.content : JSON.stringify(b.content) });
        else if (b.type === 'text') out.push({ role: 'user', content: b.text });
      }
    }
  }
  return out;
}
// OpenAI/DeepSeek response -> Anthropic-shaped response
function fromOpenAI(j) {
  const msg = j.choices && j.choices[0] && j.choices[0].message || {};
  const content = [];
  if (msg.content) content.push({ type: 'text', text: msg.content });
  for (const c of msg.tool_calls || []) {
    let input = {}; try { input = JSON.parse(c.function.arguments || '{}'); } catch (e) {}
    content.push({ type: 'tool_use', id: c.id, name: c.function.name, input });
  }
  return { content, stop_reason: (msg.tool_calls && msg.tool_calls.length) ? 'tool_use' : 'end_turn', model: j.model };
}

module.exports = async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  const prov = provider();
  if (req.method === 'GET') return res.status(200).json({ configured: !!prov, provider: prov, model: prov === 'deepseek' ? DS_MODEL : prov === 'anthropic' ? AN_MODEL : null });
  if (req.method !== 'POST') return res.status(405).json({ error: 'method_not_allowed' });
  if (!prov) return res.status(503).json({ error: 'not_configured' });

  let body = req.body;
  if (typeof body === 'string') { try { body = JSON.parse(body); } catch (e) { body = null; } }
  if (!body || !Array.isArray(body.messages) || body.messages.length === 0) return res.status(400).json({ error: 'bad_request' });
  if (JSON.stringify(body).length > MAX_BODY) return res.status(413).json({ error: 'too_large' });
  const system = String(body.system || '').slice(0, 20000);
  const messages = body.messages.slice(-24);
  const tools = Array.isArray(body.tools) ? body.tools.slice(0, 8) : [];

  try {
    if (prov === 'deepseek') {
      const r = await fetch('https://api.deepseek.com/chat/completions', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + process.env.DEEPSEEK_API_KEY, 'content-type': 'application/json' },
        body: JSON.stringify({
          model: DS_MODEL, max_tokens: 2500, temperature: 0.2,
          messages: toOpenAI(system, messages),
          tools: tools.length ? tools.map(t => ({ type: 'function', function: { name: t.name, description: t.description, parameters: t.input_schema || { type: 'object', properties: {} } } })) : undefined,
        }),
      });
      const j = await r.json();
      if (!r.ok) return res.status(r.status).json({ error: 'upstream_error', detail: j });
      return res.status(200).json(fromOpenAI(j));
    }
    const r = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: { 'x-api-key': process.env.ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
      body: JSON.stringify({ model: AN_MODEL, max_tokens: 2500, system, messages, tools: tools.length ? tools : undefined }),
    });
    const text = await r.text();
    res.status(r.status).setHeader('content-type', 'application/json');
    return res.send(text);
  } catch (e) {
    return res.status(502).json({ error: 'upstream_error', message: String(e && e.message || e) });
  }
};
