// Mã truy cập chỉ giữ trong bộ nhớ phiên hiện tại của tab, không đưa vào source/build.
export const setApiToken = (value) => { sessionStorage.setItem('aura_api_token', value.trim()) }
const authHeaders = () => { const token = sessionStorage.getItem('aura_api_token'); return token ? { 'X-Aura-Token': token } : {} }
const j = async (r) => { if (!r.ok) { let m = r.statusText; try { m = (await r.json()).detail || m } catch {} throw new Error(m) } return r.json() }
export const get = (p, q = {}) => { const s = new URLSearchParams(Object.fromEntries(Object.entries(q).filter(([, v]) => v !== undefined && v !== null && v !== ''))); return fetch(`/api/${p}${s.toString() ? '?' + s : ''}`, { headers: authHeaders() }).then(j) }
export const post = (p, body) => fetch(`/api/${p}`, { method: 'POST', headers: { 'content-type': 'application/json', ...authHeaders() }, body: JSON.stringify(body) }).then(j)
export const upload = (p, file, extra = {}) => { const fd = new FormData(); fd.append('file', file); Object.entries(extra).forEach(([k, v]) => fd.append(k, v)); return fetch(`/api/${p}`, { method: 'POST', headers: authHeaders(), body: fd }).then(j) }
