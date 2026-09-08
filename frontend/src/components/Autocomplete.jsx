import { useEffect, useRef, useState } from 'react';

export default function Autocomplete({
  searchFn,
  label,
  placeholder,
  onSelect,
  getLabel,
  value, // внешне управляемое значение (текст в поле)
  onValueChange,
}) {
  const [items, setItems] = useState([]);
  const [open, setOpen] = useState(false);
  const [focused, setFocused] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const timer = useRef(null);
  const boxRef = useRef(null);

  const triggerSearch = (query) => {
    clearTimeout(timer.current);
    timer.current = setTimeout(async () => {
      if (!query || query.trim().length < 1) {
        setItems([]);
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const res = await searchFn(query.trim());
        setItems(res);
      } catch (e) {
        setError(e.message);
        setItems([]);
      } finally {
        setLoading(false);
      }
    }, 300);
  };

  // Очищаем таймер при размонтировании, чтобы не было утечки/сетстатов
  useEffect(() => {
    return () => clearTimeout(timer.current);
  }, []);

  // Закрываем выпадающий список при клике вне
  useEffect(() => {
    const onClick = (e) => {
      if (boxRef.current && !boxRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  const handlePick = (item) => {
    setOpen(false);
    setItems([]);
    onSelect(item);
    if (onValueChange) onValueChange(getLabel(item));
  };

  return (
    <div ref={boxRef} style={{ position: 'relative' }}>
      {label && <label style={{ display: 'block', marginBottom: 4 }}>{label}</label>}
      <input
        value={value ?? ''}
        placeholder={placeholder}
        onChange={(e) => {
          onValueChange(e.target.value);
          setOpen(true);
          triggerSearch(e.target.value);
        }}
        onFocus={() => setOpen(true)}
        style={{ width: '100%', padding: 8, boxSizing: 'border-box' }}
      />
      {open && (loading || error || items.length > 0) && (
        <div
          style={{
            position: 'absolute',
            zIndex: 10,
            top: '100%',
            left: 0,
            right: 0,
            background: '#fff',
            border: '1px solid #ccc',
            maxHeight: 200,
            overflow: 'auto',
          }}
        >
          {loading && <div style={{ padding: 8, color: '#999' }}>Загрузка…</div>}
          {error && <div style={{ padding: 8, color: '#b02a37' }}>{error}</div>}
          {!loading &&
            !error &&
            items.map((item) => (
              <div
                key={item.id}
                onClick={() => handlePick(item)}
                style={{ padding: 8, cursor: 'pointer', borderBottom: '1px solid #eee' }}
                onMouseEnter={(e) => (e.target.style.background = '#f0f4f8')}
                onMouseLeave={(e) => (e.target.style.background = '#fff')}
              >
                {getLabel(item)}
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
