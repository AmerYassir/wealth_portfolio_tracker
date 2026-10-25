import { getToken, clearTokens } from '../auth.js';

const BASE = '/api/v1';

async function request(path, { method = 'GET', body } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const resp = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (resp.status === 401) {
    clearTokens();
    window.location.href = '/login';
    throw new Error('unauthorized');
  }
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`${resp.status} ${resp.statusText}: ${text}`);
  }
  if (resp.status === 204) return null;
  return resp.json();
}

export const api = {
  listPortfolios: () => request('/portfolios/'),
  getPortfolio: (id) => request(`/portfolios/${id}/`),
  listAssets: (id) => request(`/portfolios/${id}/assets/`),
  listTransactions: (id) => request(`/portfolios/${id}/transactions/`),
};

export async function login(username, password) {
  const resp = await fetch('/api/token/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!resp.ok) throw new Error('Invalid credentials');
  return resp.json();
}
