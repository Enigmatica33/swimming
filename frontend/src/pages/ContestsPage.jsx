import { useEffect, useState } from 'react';
import { createContest, fetchContests } from '../api.js';

export default function ContestsPage() {
  const [contests, setContests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [name, setName] = useState('');
  const [date, setDate] = useState('');

  const load = async () => {
    try {
      setError(null);
      setContests(await fetchContests());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await createContest({ name, date });
      setName('');
      setDate('');
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <p className="loading">Загрузка…</p>;

  return (
    <div className="card">
      <h2>Соревнования</h2>

      {error && <div className="error">{error}</div>}

      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <input
          placeholder="Название"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
        <button type="submit">Добавить</button>
      </form>

      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Название</th>
            <th>Дата</th>
            <th>Заявок</th>
          </tr>
        </thead>
        <tbody>
          {contests.map((c) => (
            <tr key={c.id}>
              <td>{c.id}</td>
              <td>{c.name}</td>
              <td>{c.date}</td>
              <td>{c.entries_count ?? 0}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
