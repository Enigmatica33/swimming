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

  const first = results[0];

  return (
    <div className="card">
      <h2>Результаты</h2>

      {error && <div className="error">{error}</div>}

      {first && (
        <p className="contest-info">
          <strong>{first.contest_name}</strong>{' '}
          {first.contest_date || ''}
        </p>
      )}

      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Пловец</th>
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
              <td>{r.race_number ?? '—'}</td>
              <td>{r.path_number ?? '—'}</td>
              <td>{r.result_time_display || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
