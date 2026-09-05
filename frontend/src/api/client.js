const RAW = (import.meta.env.VITE_API_URL || '').replace(/\/+$/, '')
const BASE = RAW ? `${RAW}${RAW.endsWith('/api') ? '' : '/api'}` : '/api'

async function request(path, options = {}) {
  const url = `${BASE}${path}`
  let res
  try {
    res = await fetch(url, {
      headers: { 'Content-Type': 'application/json', ...options.headers },
      ...options,
    })
  } catch (err) {
    throw new Error(`Network error — ${url} unreachable. Is the backend running? (${err.message})`)
  }
  if (!res.ok) {
    let detail
    try {
      const body = await res.json()
      detail = body.detail
    } catch {
      detail = await res.text().catch(() => res.statusText)
    }
    throw new Error(`${res.status} ${detail || res.statusText} — ${url}`)
  }
  return res.json()
}

export const api = {
  health: () => request('/health'),

  getModels: () => request('/models'),
  getDefaultModel: () => request('/settings/default-model'),
  setDefaultModel: (model) =>
    request('/settings/default-model', { method: 'PUT', body: JSON.stringify({ default_model: model }) }),

  analyzeYouTube: (body) =>
    request('/media/youtube', { method: 'POST', body: JSON.stringify(body) }),

  analyzeSpotify: (body) =>
    request('/media/spotify', { method: 'POST', body: JSON.stringify(body) }),

  transcribeFile: (formData) => {
    const url = `${BASE}/media/transcribe`
    return fetch(url, { method: 'POST', body: formData }).then(async (r) => {
      if (!r.ok) {
        const text = await r.text().catch(() => r.statusText)
        throw new Error(`${r.status} ${text} — ${url}`)
      }
      return r.json()
    })
  },

  analyzeSocial: (platform, target, pattern, model) =>
    request(`/social/${platform}?target=${encodeURIComponent(target)}&pattern=${encodeURIComponent(pattern)}${model ? `&model=${encodeURIComponent(model)}` : ''}`, { method: 'POST' }),

  scrapeWeb: (body) =>
    request('/web/scrape', { method: 'POST', body: JSON.stringify(body) }),

  analyzeDomain: (body) =>
    request('/web/domain', { method: 'POST', body: JSON.stringify(body) }),

  analyzeEmailHeaders: (body) =>
    request('/web/email-headers', { method: 'POST', body: JSON.stringify(body) }),

  analyzeLogs: (body) =>
    request('/web/logs', { method: 'POST', body: JSON.stringify(body) }),

  getResults: (limit = 20, offset = 0) =>
    request(`/results?limit=${limit}&offset=${offset}`),

  getResult: (id) => request(`/results/${id}`),
}