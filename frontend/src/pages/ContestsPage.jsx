import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  createContest,
  fetchContests,
  finalProtocolUrl,
  startProtocolUrl,
} from '../api.js';
import useFetch from '../hooks/useFetch.js';

export default function ContestsPage() {
  const { data, loading, error, setError, reload } = useFetch(fetchContests);
  const contests = data ?? [];

  const [name, setName] = useState('');
  const [date, setDate] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await createContest({ name, date });
      setName('');
      setDate('');
      await reload();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <p className="loading">Загрузка…</p>;

  return (
    <div className="card">
      <h2>Соревнования</h2>

      {error && <div className="error">{error}</div>}

      <form
        onSubmit={handleSubmit}
        style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}
      >
        <input
          placeholder="Название"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          required
        />
        <button type="submit">Добавить</button>
      </form>

      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Название</th>
            <th>Дата</th>
            <th>Заявок</th>
            <th>Протоколы</th>
          </tr>
        </thead>
        <tbody>
          {contests.map((c) => (
            <tr key={c.id}>
              <td>{c.id}</td>
              <td>
                <Link className="no-underline" to={`/results/${c.id}`}>
                  {c.name}
                </Link>
              </td>
              <td>{c.date}</td>
              <td>{c.entries_count ?? 0}</td>
              <td>
                <a href={startProtocolUrl(c.id)} className="btn-link">
                  Стартовый
                </a>
                {' · '}
                <a href={finalProtocolUrl(c.id)} className="btn-link">
                  Итоговый
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
