import useFetch from '../hooks/useFetch.js';
import { fetchCoaches } from '../api.js';
import { fullName } from '../helpers.js';

export default function CoachesPage() {
  const { data, loading, error } = useFetch(fetchCoaches);
  const coaches = data ?? [];

  if (loading) return <p className="loading">Загрузка…</p>;

  return (
    <div className="card">
      <h2>Тренеры</h2>

      {error && <div className="error">{error}</div>}

      {coaches.length === 0 && !error && (
        <p className="loading">Тренеров пока нет.</p>
      )}

      {coaches.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>ФИО</th>
              <th>Клуб</th>
              <th>Пловцов</th>
              <th className="right-align">Призовые места</th>
            </tr>
          </thead>
          <tbody>
            {coaches.map((c) => (
              <tr key={c.id}>
                <td>{fullName(c)}</td>
                <td>{c.club_name || '—'}</td>
                <td>{c.swimmers_count ?? 0}</td>
                <td className="right-align">{c.prize_places ?? 0}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
