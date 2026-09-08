"""Общие утилиты бэкенда (единые точки реализации без дублирования)."""

from __future__ import annotations

from datetime import date


def format_swim_time(value) -> str | None:
    """Форматирует время заплыва: '15,50' или '1,11,59' (если есть минуты).

    Принимает timedelta/длительность; для None возвращает None.
    """
    if value is None:
        return None
    total_us = (
        value.days * 86_400_000_000
        + value.seconds * 1_000_000
        + value.microseconds
    )
    minutes, rem = divmod(total_us, 60_000_000)
    seconds, frac_us = divmod(rem, 1_000_000)
    hundredths = frac_us // 10_000
    if minutes:
        return f'{minutes},{seconds:02d},{hundredths:02d}'
    return f'{seconds},{hundredths:02d}'


def age_on_date(dob, reference_date):
    """Полное количество лет на reference_date.

    Принимает дату или строку ISO ('YYYY-MM-DD'); для None возвращает None.
    """
    if dob is None:
        return None
    if isinstance(dob, str):
        dob = date.fromisoformat(dob)
    return (
        reference_date.year
        - dob.year
        - ((reference_date.month, reference_date.day) < (dob.month, dob.day))
    )
