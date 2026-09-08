import { useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  fetchResults,
  finalProtocolUrl,
  startProtocolUrl,
} from '../api.js';
import SwimmerCard from '../components/SwimmerCard.jsx';
import useFetch from '../hooks/useFetch.js';
import { compareByTime, isTopThree } from '../helpers.js';

export default function ResultsPage() {
  const { id } = useParams();
  const { data, loading, error } = useFetch(
    () => (id ? fetchResults(id) : Promise.resolve([])),
    [id]
  );
  const results = data ?? [];

  const [selectedSwimmer, setSelectedSwimmer] = useState(null);

  // Выбранные фильтры (null = показать все)
  const [coachFilter, setCoachFilter] = useState(null);
  const [categoryFilter, setCategoryFilter] = useState(null);

  // Порядок полов: девочки/женщины ('0_*') идут раньше мальчиков/мужчин ('1_*')
  const genderOrder = (g) => (String(g).startsWith('0') ? 0 : 1);

  // Общий компаратор категорий: дистанция → возрастная группа → пол
  const compareCategories = (a, b) => {
    const dist = (a.distance ?? 0) - (b.distance ?? 0);
    if (dist !== 0) return dist;
    const age = (a.age_group ?? 0) - (b.age_group ?? 0);
    if (age !== 0) return age;
    return genderOrder(a.gender) - genderOrder(b.gender);
  };

  // Списки тренеров и категорий, встречающихся в результатах
  const { coaches, categories } = useMemo(() => {
    const coachMap = new Map();
    const catMap = new Map();

    results.forEach((r) => {
      if (r.coach) {
        coachMap.set(r.coach, {
          id: r.coach,
          name: r.coach_name || `Тренер № ${r.coach}`,
        });
      }
      if (r.category) {
        catMap.set(r.category, {
          id: r.category,
          title: r.category_title || `Категория № ${r.category}`,
          distance: r.distance ?? 0,
          gender: r.gender,
          age_group: r.age_group,
        });
      }
    });

    const coachList = [...coachMap.values()].sort((a, b) =>
      a.name.localeCompare(b.name, 'ru')
    );
    const catList = [...catMap.values()].sort(compareCategories);

    return { coaches: coachList, categories: catList };
  }, [results]);

  // Применяем выбранные фильтры
  const filtered = useMemo(() => {
    return results.filter((r) => {
      if (coachFilter !== null && r.coach !== coachFilter) return false;
      if (categoryFilter !== null && r.category !== categoryFilter) return false;
      return true;
    });
  }, [results, coachFilter, categoryFilter]);

  // Фактическое место каждого пловца в своей категории
  // (считается по ВСЕМ результатам, без учёта активных фильтров)
  const placeMap = useMemo(() => {
    const map = new Map();
    const byCategory = new Map();

    results.forEach((r) => {
      const key = r.category;
      if (!byCategory.has(key)) byCategory.set(key, []);
      byCategory.get(key).push(r);
    });

    byCategory.forEach((items) => {
      items.sort(compareByTime);
      items.forEach((r, i) => map.set(r.id, i + 1));
    });

    return map;
  }, [results]);

  // Группируем по категории и сортируем внутри от первого места к последнему
  const grouped = useMemo(() => {
    const map = new Map();
    filtered.forEach((r) => {
      const key = r.category;
      if (!map.has(key)) {
        map.set(key, {
          id: r.category,
          title: r.category_title || 'Без категории',
          distance: r.distance ?? 0,
          gender: r.gender,
          age_group: r.age_group,
          items: [],
        });
      }
      map.get(key).items.push(r);
    });

    const groups = [...map.values()];
    groups.forEach((g) => {
      // Первое место — самый быстрый результат; без времени — в конце
      g.items.sort(compareByTime);
    });

    groups.sort(compareCategories);

    return groups;
  }, [filtered]);

  const toggleCoach = (id) => setCoachFilter((cur) => (cur === id ? null : id));
  const toggleCategory = (id) =>
    setCategoryFilter((cur) => (cur === id ? null : id));

  if (loading) return <p className="loading">Загрузка…</p>;

  if (!id) {
    return (
      <div className="card">
        <h2>Результаты</h2>
        <p>
          Выберите соревнование в разделе{' '}
          <Link to="/contests">Соревнования</Link>.
        </p>
      </div>
    );
  }

  const first = results[0];

  return (
    <div className="card">
      <h2>Результаты</h2>

      {error && <div className="error">{error}</div>}

      {first && (
        <>
          <p className="contest-info">
            <strong>{first.contest_name}</strong> {first.contest_date || ''}
          </p>
          <div className="protocol-actions">
            <a href={startProtocolUrl(id)} className="btn-link">
              Скачать стартовый протокол
            </a>
            <a href={finalProtocolUrl(id)} className="btn-link">
              Скачать итоговый протокол
            </a>
          </div>
        </>
      )}

      {/* Фильтр по тренеру */}
      <div className="filter-group">
        <div className="filter-label">Тренер</div>
        <div className="filter-btns">
          <button
            type="button"
            className={`filter-btn ${coachFilter === null ? 'active' : ''}`}
            onClick={() => setCoachFilter(null)}
          >
            Все
          </button>
          {coaches.map((c) => (
            <button
              key={c.id}
              type="button"
              className={`filter-btn ${coachFilter === c.id ? 'active' : ''}`}
              onClick={() => toggleCoach(c.id)}
            >
              {c.name}
            </button>
          ))}
        </div>
      </div>

      {/* Фильтр по категории */}
      <div className="filter-group">
        <div className="filter-label">Категория</div>
        <div className="filter-btns">
          <button
            type="button"
            className={`filter-btn ${categoryFilter === null ? 'active' : ''}`}
            onClick={() => setCategoryFilter(null)}
          >
            Все
          </button>
          {categories.map((c) => (
            <button
              key={c.id}
              type="button"
              className={`filter-btn ${
                categoryFilter === c.id ? 'active' : ''
              }`}
              onClick={() => toggleCategory(c.id)}
            >
              {c.title}
            </button>
          ))}
        </div>
      </div>

      {grouped.length === 0 && (
        <p className="loading">По заданным фильтрам результатов нет.</p>
      )}

      {grouped.map((group) => (
        <div key={group.id} className="category-block">
          <h3 className="category-title">{group.title}</h3>
          <table>
            <thead>
              <tr>
                <th aria-label="Место" />
                <th aria-label="Пловец" />
                <th className="right-align">Результат</th>
                <th className="right-align">Заявка</th>
              </tr>
            </thead>
            <tbody>
              {group.items.map((r) => {
                const place = placeMap.get(r.id);
                const topThree = isTopThree(place);
                return (
                  <tr key={r.id} className={topThree ? 'top-three' : ''}>
                    <td className="place-badge">
                      {place}
                      {topThree && (
                        <span
                          className={`medal medal-${place}`}
                          aria-label={`место ${place}`}
                        >
                          {place === 1 ? '🥇' : place === 2 ? '🥈' : '🥉'}
                        </span>
                      )}
                    </td>
                    <td>
                      {r.swimmer ? (
                        <button
                          type="button"
                          className="swimmer-link"
                          onClick={() =>
                            setSelectedSwimmer({
                              id: r.swimmer,
                              name: r.swimmer_name,
                            })
                          }
                        >
                          {r.swimmer_name}
                        </button>
                      ) : (
                        r.swimmer_name
                      )}
                    </td>
                    <td className="right-align">
                      {r.result_time_display || '—'}
                    </td>
                    <td className="right-align">
                      {r.stated_time_display || '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ))}

      {selectedSwimmer && (
        <SwimmerCard
          swimmerId={selectedSwimmer.id}
          onClose={() => setSelectedSwimmer(null)}
        />
      )}
    </div>
  );
}
