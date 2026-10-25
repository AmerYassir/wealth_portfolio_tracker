import { getToken, clearTokens } from '../auth.js';

const BASE = '/api/v1';

async function request(path, { method = 'GET', body } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const resp = await fetch(`${BASE}${path}`, { method, headers, body: body ? JSON.stringify(body) : undefined });
  if (resp.status === 401) { clearTokens(); window.location.href = '/login'; throw new Error('unauthorized'); }
  if (!resp.ok) { const text = await resp.text(); throw new Error(`${resp.status}: ${text}`); }
  if (resp.status === 204) return null;
  return resp.json();
}

export const api = {
  listPortfolios: () => request('/portfolios/'),
  getPortfolio: (id) => request(`/portfolios/${id}/`),
  createPortfolio: (name) => request('/portfolios/', { method: 'POST', body: { name } }),
  listAssets: (id) => request(`/portfolios/${id}/assets/`),
  createAsset: (id, asset) => request(`/portfolios/${id}/assets/`, { method: 'POST', body: asset }),
  deleteAsset: (id, assetId) => request(`/portfolios/${id}/assets/${assetId}/`, { method: 'DELETE' }),
  listTransactions: (id) => request(`/portfolios/${id}/transactions/`),
  createTransaction: (id, tx) => request(`/portfolios/${id}/transactions/`, { method: 'POST', body: tx }),
  deleteTransaction: (id, txId) => request(`/portfolios/${id}/transactions/${txId}/`, { method: 'DELETE' }),
  listMembers: (id) => request(`/portfolios/${id}/members/`),
  inviteMember: (id, username, role) => request(`/portfolios/${id}/members/`, { method: 'POST', body: { username, role } }),
  removeMember: (id, memberId) => request(`/portfolios/${id}/members/${memberId}/`, { method: 'DELETE' }),
};

export async function login(username, password) {
  const resp = await fetch('/api/token/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password }) });
  if (!resp.ok) throw new Error('Invalid credentials');
  return resp.json();
}

export async function register(username, password, email) {
  const resp = await fetch('/api/token/register/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password, email }) });
  if (!resp.ok) { const body = await resp.json().catch(() => ({})); const msg = Object.values(body).flat?.().join(' ') || 'Registration failed'; throw new Error(msg); }
  return resp.json();
}
