import { useMemo } from 'react';
import { fetchSwimmerHistory } from '../api.js';
import useFetch from '../hooks/useFetch.js';
import {
  genderLabel,
  isTopThree,
  placeClass,
} from '../helpers.js';

export default function SwimmerCard({ swimmerId, onClose }) {
  const { data, loading, error } = useFetch(
    () => fetchSwimmerHistory(swimmerId),
    [swimmerId]
  );

  // Сводная статистика и динамика по соревнованиям
  const stats = useMemo(() => {
    if (!data) return null;
    const places = [];
    data.contests.forEach((c) =>
      c.results.forEach((r) => {
        if (r.place != null) places.push(r.place);
      })
    );
    const best = places.length ? Math.min(...places) : null;
    const podiums = places.filter((p) => p >= 1 && p <= 3).length;

    // Лучшее место в каждом соревновании (для визуализации динамики)
    const dynamics = data.contests.map((c) => {
      const bestInContest = c.results
        .map((r) => r.place)
        .filter((p) => p != null);
      return {
        contest_name: c.contest_name,
        contest_date: c.contest_date,
        best: bestInContest.length ? Math.min(...bestInContest) : null,
      };
    });

    return { starts: places.length, best, podiums, dynamics };
  }, [data]);

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <button type="button" className="modal-close" onClick={onClose}>
          ✕
        </button>

        {loading && <p className="loading">Загрузка…</p>}
        {error && <div className="error">{error}</div>}

        {data && (
          <>
            <h2>
              {data.last_name} {data.first_name}
            </h2>

            <dl className="swimmer-info">
              <div>
                <dt>Дата рождения</dt>
                <dd>{data.date_of_birth || '—'}</dd>
              </div>
              <div>
                <dt>Возраст</dt>
                <dd>{data.age ?? '—'}</dd>
              </div>
              <div>
                <dt>Пол</dt>
                <dd>{genderLabel(data.gender)}</dd>
              </div>
              <div>
                <dt>Клуб</dt>
                <dd>{data.club_name || '—'}</dd>
              </div>
              <div>
                <dt>Тренер</dt>
                <dd>{data.coach_name || '—'}</dd>
              </div>
            </dl>

            {stats && (
              <div className="summary-cards">
                <div className="summary-card">
                  <span className="summary-value">{stats.starts}</span>
                  <span className="summary-label">Всего стартов</span>
                </div>
                <div className="summary-card">
                  <span className="summary-value">{stats.podiums}</span>
                  <span className="summary-label">Подиумов (1–3)</span>
                </div>
                <div className="summary-card">
                  <span className="summary-value">
                    {stats.best ?? '—'}
                  </span>
                  <span className="summary-label">Лучшее место</span>
                </div>
              </div>
            )}

            {stats && stats.dynamics.length > 0 && (
              <div className="dynamics">
                <h3>Динамика мест по соревнованиям</h3>
                <div className="dynamics-row">
                  {stats.dynamics.map((d, i) => (
                    <div key={i} className="dynamics-item">
                      <span
                        className={`dynamics-dot ${placeClass(d.best)}`}
                      >
                        {d.best ?? '—'}
                      </span>
                      <span className="dynamics-name">{d.contest_name}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="history">
              <h3>Соревнования и результаты</h3>
              {data.contests.length === 0 && (
                <p className="loading">Пловец ещё не участвовал в зачёте.</p>
              )}
              {data.contests.map((c) => (
                <div key={c.contest} className="history-contest">
                  <h4>
                    {c.contest_name}{' '}
                    {c.contest_date ? (
                      <span className="muted">({c.contest_date})</span>
                    ) : null}
                  </h4>
                  <table>
                    <thead>
                      <tr>
                        <th className="right-align">Категория</th>
                        <th className="right-align">Результат</th>
                        <th className="right-align">Заявка</th>
                        <th className="right-align">Место</th>
                      </tr>
                    </thead>
                    <tbody>
                      {c.results.map((r) => (
                        <tr
                          key={r.id}
                          className={isTopThree(r.place) ? 'top-three' : ''}
                        >
                          <td>{r.category_title || '—'}</td>
                          <td className="right-align">
                            {r.result_time_display || '—'}
                          </td>
                          <td className="right-align">
                            {r.stated_time_display || '—'}
                          </td>
                          <td className="right-align">
                            <span className={`place-value ${placeClass(r.place)}`}>
                              {r.place ?? '—'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
