// Общие константы и утилиты фронтенда (единые источники без дублирования).

export const GENDER_LABELS = {
  '1_boys': 'Мальчики',
  '0_girls': 'Девочки',
  '1_young_men': 'Юноши',
  '0_young_women': 'Девушки',
  '1_men': 'Мужчины',
  '0_women': 'Женщины',
};

export const GENDER_OPTIONS = [
  { value: '1_men', label: 'Мужской' },
  { value: '0_women', label: 'Женский' },
];

export function genderLabel(value) {
  return GENDER_LABELS[value] || value || '—';
}

export function fullName(person) {
  return `${person.last_name} ${person.first_name}`.trim();
}

export function isTopThree(place) {
  return place != null && place >= 1 && place <= 3;
}

/** Сравнение результатов по времени; без времени — в конец. */
export function compareByTime(a, b) {
  if (a.result_time_us == null && b.result_time_us == null) return 0;
  if (a.result_time_us == null) return 1;
  if (b.result_time_us == null) return -1;
  return a.result_time_us - b.result_time_us;
}

export function placeClass(place) {
  if (place === 1) return 'p1';
  if (place === 2) return 'p2';
  if (place === 3) return 'p3';
  return '';
}
