import { useEffect, useState } from 'react';
import { fetchResults } from '../api.js';

export default function ResultsPage() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        setResults(await fetchResults());
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <p className="loading">Загрузка…</p>;

  return (
    <div className="card">
      <h2>Результаты</h2>

      {error && <div className="error">{error}</div>}

      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Пловец</th>
            <th>Соревнование</th>
            <th>Категория</th>
            <th>Стиль</th>
            <th>Заплыв</th>
            <th>Дорожка</th>
            <th>Время</th>
          </tr>
        </thead>
        <tbody>
          {results.map((r) => (
            <tr key={r.id}>
              <td>{r.id}</td>
              <td>{r.swimmer_name}</td>
              <td>{r.contest_name}</td>
              <td>{r.category_title || '—'}</td>
              <td>{r.swimstyle_name || '—'}</td>
              <td>{r.race_number ?? '—'}</td>
              <td>{r.path_number ?? '—'}</td>
              <td>{r.result_time || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
