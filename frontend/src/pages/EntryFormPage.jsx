import { useEffect, useState } from 'react';
import Autocomplete from '../components/Autocomplete.jsx';
import {
  createEntry,
  resolveCategory,
  searchClubs,
  searchCoaches,
} from '../api.js';

const GENDERS = [
  { value: '1_men', label: 'Мужской' },
  { value: '0_women', label: 'Женский' },
];

export default function EntryFormPage() {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [gender, setGender] = useState('1_men');
  const [dob, setDob] = useState('');
  const [age, setAgeInput] = useState('');
  const [coach, setCoach] = useState(null);
  const [club, setClub] = useState(null);
  const [coachSearch, setCoachSearch] = useState('');
  const [clubSearch, setClubSearch] = useState('');

  const [category, setCategory] = useState(null);
  const [resolvedAge, setResolvedAge] = useState(null);

  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // Автоопределение категории по полу, дате рождения или возрасту
  useEffect(() => {
    const resolve = async () => {
      const payload = { gender };
      if (dob) {
        payload.date_of_birth = dob;
      } else if (age) {
        payload.age = Number(age);
      }

      try {
        const res = await resolveCategory(payload);
        setCategory(res.category_title);
        setResolvedAge(res.age);
      } catch {
        setCategory(null);
        setResolvedAge(null);
      }
    };
    resolve();
  }, [gender, dob, age]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!firstName.trim() || !lastName.trim()) {
      setError('Укажите имя и фамилию.');
      return;
    }
    if (!dob && !age) {
      setError('Укажите дату рождения или возраст.');
      return;
    }

    const payload = {
      swimmer: {
        first_name: firstName,
        last_name: lastName,
        gender,
        date_of_birth: dob || null,
        coach: coach?.id || null,
        club: club?.id || null,
      },
      manual_age: dob ? null : age ? Number(age) : null,
    };

    setSubmitting(true);
    try {
      const created = await createEntry(payload);
      setSuccess(
        `Заявка #${created.id} принята. Категория: ${created.category_title || 'не определена'}.`
      );
      setFirstName('');
      setLastName('');
      setDob('');
      setAgeInput('');
      setCoach(null);
      setClub(null);
      setCoachSearch('');
      setClubSearch('');
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="card">
      <h2>Подать заявку на соревнование</h2>
      <p>Заполните данные — категория и дистанция определятся автоматически.</p>

      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}

      <form onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gap: 8 }}>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              placeholder="Имя"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              required
              style={{ flex: 1 }}
            />
            <input
              placeholder="Фамилия"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              required
              style={{ flex: 1 }}
            />
          </div>

          <div style={{ display: 'flex', gap: 8 }}>
            <select value={gender} onChange={(e) => setGender(e.target.value)}>
              {GENDERS.map((g) => (
                <option key={g.value} value={g.value}>
                  {g.label}
                </option>
              ))}
            </select>
            <input
              type="date"
              placeholder="Дата рождения"
              value={dob}
              onChange={(e) => {
                setDob(e.target.value);
                if (e.target.value) setAgeInput('');
              }}
              style={{ flex: 1 }}
            />
            <input
              type="number"
              min="3"
              max="100"
              placeholder="или возраст"
              value={age}
              onChange={(e) => {
                setAgeInput(e.target.value);
                if (e.target.value) setDob('');
              }}
              style={{ flex: 1 }}
            />
          </div>

          <Autocomplete
            searchFn={searchCoaches}
            label="Тренер (необязательно)"
            placeholder="Фамилия тренера…"
            value={coachSearch}
            onValueChange={setCoachSearch}
            onSelect={setCoach}
            getLabel={(c) => `${c.last_name} ${c.first_name}`}
          />
          <Autocomplete
            searchFn={searchClubs}
            label="Клуб (необязательно)"
            placeholder="Название клуба…"
            value={clubSearch}
            onValueChange={setClubSearch}
            onSelect={setClub}
            getLabel={(c) => c.name}
          />
        </div>

        <div className="card" style={{ background: '#f0f4f8', marginTop: 16 }}>
          <strong>Категория:</strong>{' '}
          {category ? category : resolvedAge != null ? 'не определена' : '—'}
          {resolvedAge != null && <span> · возраст: {resolvedAge}</span>}
        </div>

        <button type="submit" disabled={submitting}>
          {submitting ? 'Отправка…' : 'Подать заявку'}
        </button>
      </form>
    </div>
  );
}
