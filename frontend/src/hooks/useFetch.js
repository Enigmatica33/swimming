import { useCallback, useEffect, useState } from 'react';

/**
 * Универсальный хук загрузки данных.
 *
 * Централизует типовой паттерн «data + loading + error» и повторную
 * загрузку (reload), который раньше дублировался в каждой странице.
 *
 * @param {() => Promise<any>} fetcher функция-загрузчик данных
 * @param {Array} deps зависимости, при изменении которых перезагрузить данные
 * @returns {{ data, setData, loading, error, reload }}
 */
export default function useFetch(fetcher, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tick, setTick] = useState(0);

  const reload = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    const load = async () => {
      try {
        const result = await fetcher();
        if (active) setData(result);
      } catch (e) {
        if (active) setError(e.message);
      } finally {
        if (active) setLoading(false);
      }
    };

    load();

    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  return { data, setData, loading, error, setError, reload };
}
