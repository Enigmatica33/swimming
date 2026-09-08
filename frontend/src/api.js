const BASE_URL = '/api/v1';

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });

  if (!res.ok) {
    const text = await res.text();
    let detail;
    try {
      const data = JSON.parse(text);
      detail = data.detail || data.non_field_errors || data.message || text;
    } catch {
      detail = text;
    }
    if (Array.isArray(detail)) detail = detail.join('; ');
    throw new Error(detail);
  }

  if (res.status === 204) {
    return null;
  }

  return res.json();
}

// DRF возвращает либо массив, либо { results: [...] } при пагинации
function extractList(data) {
  return Array.isArray(data) ? data : (data?.results ?? []);
}

// --- Общий поиск для автокомплита ---
async function search(resource, query) {
  const q = query ? `?search=${encodeURIComponent(query)}` : '';
  return extractList(await request(`/${resource}/${q}`));
}

// --- Соревнования ---
export const fetchContests = () => request('/contests/');
export const searchContests = (q) => search('contests', q);
export const createContest = (data) =>
  request('/contests/', { method: 'POST', body: JSON.stringify(data) });

// --- Пловцы ---
export const fetchSwimmers = () => request('/swimmers/');
export const searchSwimmers = (q) => search('swimmers', q);
export const createSwimmer = (data) =>
  request('/swimmers/', { method: 'POST', body: JSON.stringify(data) });

// --- Карточка пловца (данные + история результатов) ---
export const fetchSwimmerHistory = (id) =>
  request(`/swimmers/${id}/history/`);

// --- Тренеры ---
export const searchCoaches = (q) => search('coaches', q);
export const fetchCoaches = () => request('/coaches/');

// --- Клубы ---
export const searchClubs = (q) => search('clubs', q);

// --- Стили плавания ---
export const fetchSwimstyles = () => request('/swim_styles/');

// --- Заявки ---
export const fetchEntries = () => request('/entries/');
export const createEntry = (data) =>
  request('/entries/', { method: 'POST', body: JSON.stringify(data) });

// --- Определение категории ---
export const resolveCategory = (data) =>
  request('/entries/resolve-category/', {
    method: 'POST',
    body: JSON.stringify(data),
  });

// --- Результаты (по соревнованию; без id — все) ---
export const fetchResults = (contestId) => {
  const q = contestId ? `?contest=${encodeURIComponent(contestId)}` : '';
  return request(`/results/${q}`);
};

// --- Ссылки на протоколы соревнования (PDF) ---
export const startProtocolUrl = (contestId) =>
  `${BASE_URL}/contests/${contestId}/start-protocol/`;

export const finalProtocolUrl = (contestId) =>
  `${BASE_URL}/contests/${contestId}/final-protocol/`;
