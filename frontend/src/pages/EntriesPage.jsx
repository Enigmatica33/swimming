import { Link } from 'react-router-dom';
import { fetchEntries } from '../api.js';
import useFetch from '../hooks/useFetch.js';

export default function EntriesPage() {
  const { data, loading, error } = useFetch(fetchEntries);
  const entries = data ?? [];

  if (loading) return <p className="loading">Загрузка…</p>;

  return (
    <div className="card">
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <h2>Заявки</h2>
        <Link to="/entries/new">
          <button>+ Подать заявку</button>
        </Link>
      </div>

      {error && <div className="error">{error}</div>}

      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Пловец</th>
            <th>Возраст</th>
            <th>Дистанция</th>
            <th>Категория</th>
            <th>Одобрена</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((en) => (
            <tr key={en.id}>
              <td>{en.id}</td>
              <td>{en.swimmer_name}</td>
              <td>{en.age ?? '—'}</td>
              <td>{en.distance} м</td>
              <td>{en.category_title || '—'}</td>
              <td>{en.is_approved ? '✅' : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
