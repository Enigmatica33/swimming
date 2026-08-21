import { useEffect, useState } from 'react';
import { createSwimmer, fetchSwimmers } from '../api.js';

export default function SwimmersPage() {
  const [swimmers, setSwimmers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [first_name, setFirstName] = useState('');
  const [last_name, setLastName] = useState('');
  const [gender, setGender] = useState('1_men');
  const [date_of_birth, setDateOfBirth] = useState('');

  const load = async () => {
    try {
      setError(null);
      setSwimmers(await fetchSwimmers());
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
      await createSwimmer({
        first_name,
        last_name,
        gender,
        date_of_birth: date_of_birth || null,
      });
      setFirstName('');
      setLastName('');
      setDateOfBirth('');
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <p className="loading">Загрузка…</p>;

  return (
    <div className="card">
      <h2>Пловцы</h2>

      {error && <div className="error">{error}</div>}

      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <input
          placeholder="Имя"
          value={first_name}
          onChange={(e) => setFirstName(e.target.value)}
          required
        />
        <input
          placeholder="Фамилия"
          value={last_name}
          onChange={(e) => setLastName(e.target.value)}
          required
        />
        <select value={gender} onChange={(e) => setGender(e.target.value)}>
          <option value="1_men">Мужчины</option>
          <option value="0_women">Женщины</option>
        </select>
        <input
          type="date"
          value={date_of_birth}
          onChange={(e) => setDateOfBirth(e.target.value)}
        />
        <button type="submit">Добавить</button>
      </form>

      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Имя</th>
            <th>Фамилия</th>
            <th>Пол</th>
            <th>Дата рождения</th>
            <th>Возраст</th>
          </tr>
        </thead>
        <tbody>
          {swimmers.map((s) => (
            <tr key={s.id}>
              <td>{s.id}</td>
              <td>{s.first_name}</td>
              <td>{s.last_name}</td>
              <td>{s.gender}</td>
              <td>{s.date_of_birth || '—'}</td>
              <td>{s.age ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
