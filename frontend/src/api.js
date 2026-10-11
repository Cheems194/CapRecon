const BASE_URL = 'http://127.0.0.1:8000/api';

export async function request(endpoint, options = {}, orgSlug = null) {
  const headers = {
    ...(options.headers || {}),
  };

  if (orgSlug) {
    headers['X-Organization'] = orgSlug;
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const errorMsg = data?.error || data?.detail || `Request failed with status ${response.status}`;
    const error = new Error(errorMsg);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

export function getOrganizations() {
  return request('/organizations/');
}

export function getTransactions(orgSlug) {
  return request('/transactions/', {}, orgSlug);
}

export function getLineItems(orgSlug) {
  return request('/line-items/', {}, orgSlug);
}

export function importBankStatement(orgSlug, file) {
  const formData = new FormData();
  formData.append('file', file);

  return request('/bank-statements/import/', {
    method: 'POST',
    body: formData,
  }, orgSlug);
}

export function approveMatch(orgSlug, matchId) {
  return request(`/matches/${matchId}/approve/`, {
    method: 'POST',
  }, orgSlug);
}

export function rejectMatch(orgSlug, matchId) {
  return request(`/matches/${matchId}/reject/`, {
    method: 'POST',
  }, orgSlug);
}

export function ignoreTransaction(orgSlug, txId) {
  return request(`/transactions/${txId}/ignore/`, {
    method: 'POST',
  }, orgSlug);
}

export function formatMoney(amount) {
  const num = parseFloat(amount);
  if (isNaN(num)) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(num);
}
