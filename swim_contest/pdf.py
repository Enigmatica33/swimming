"""Генерация протоколов соревнований в PDF.

Протоколы строятся из HTML-шаблонов (templates/protocols/) и рендерятся
в PDF через xhtml2pdf. Для корректного отображения кириллицы шрифт
регистрируется в reportlab (см. _ensure_font_registered) и используется
в шаблонах по имени FONT_NAME.
"""

from __future__ import annotations

import os
from collections import defaultdict
from datetime import timedelta
from functools import lru_cache
from io import BytesIO

from django.template.loader import render_to_string
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from xhtml2pdf import default as xhtml2pdf_default
from xhtml2pdf import pisa

from .models import Result
from .services import compute_places_for_contest
from .utils import format_swim_time

# Имя семейства шрифта, используемого в шаблонах протоколов.
FONT_NAME = 'ProtocolFont'

# Возможные пути к шрифту с поддержкой кириллицы (порядок поиска).
_FONT_CANDIDATES = (
    r'C:\Windows\Fonts\arial.ttf',  # Windows
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Debian/Ubuntu
    '/usr/share/fonts/dejavu/DejaVuSans.ttf',
    '/Library/Fonts/Arial Unicode.ttf',  # macOS
)

_font_registered = False


@lru_cache(maxsize=1)
def _font_path() -> str:
    """Возвращает путь к TTF-шрифту с поддержкой кириллицы."""
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    raise RuntimeError(
        'Не найден системный шрифт с поддержкой кириллицы для PDF.'
    )


def _ensure_font_registered():
    """Регистрирует кириллический шрифт в reportlab и xhtml2pdf."""
    global _font_registered
    if _font_registered:
        return
    pdfmetrics.registerFont(TTFont(FONT_NAME, _font_path()))
    pdfmetrics.registerFontFamily(
        FONT_NAME,
        normal=FONT_NAME,
        bold=FONT_NAME,
        italic=FONT_NAME,
        boldItalic=FONT_NAME,
    )
    # Чтобы xhtml2pdf распознавал CSS font-family: ProtocolFont.
    xhtml2pdf_default.DEFAULT_FONT[FONT_NAME.lower()] = FONT_NAME
    _font_registered = True


# Порядок полов для сортировки категорий в итоговом протоколе.
GENDER_ORDER = {
    gender: i
    for i, gender in enumerate(
        (
            '0_girls',
            '0_young_women',
            '0_women',
            '1_boys',
            '1_young_men',
            '1_men',
        )
    )
}


def _category_sort_key(category):
    """Ключ сортировки категорий: дистанция → возраст → пол."""
    return (
        category.distance,
        category.age_group,
        GENDER_ORDER.get(category.gender, 99),
    )


def _results_for(contest):
    return list(
        Result.objects.with_entry_details().filter(entry__contest=contest)
    )


def _swimmer_full_name(swimmer) -> str:
    return f'{swimmer.last_name} {swimmer.first_name}'.strip()


def _row_base(r) -> dict:
    """Общая часть строки протокола (пловец, клуб, заявка)."""
    swimmer = r.entry.swimmer
    return {
        'swimmer': _swimmer_full_name(swimmer),
        'club': str(swimmer.club) if swimmer.club else '',
        'stated': format_swim_time(r.entry.stated_time) or '',
    }


def _build_final_context(contest):
    """Контекст шаблона итогового протокола.

    Категории сортируются (дистанция → возраст → пол), внутри каждой —
    от 1-го места к последнему (самый быстрый результат первым).
    """
    results = _results_for(contest)
    places = compute_places_for_contest(contest)

    groups = defaultdict(list)
    for r in results:
        groups[r.entry.category].append(r)

    categories = []
    for category in sorted(groups, key=_category_sort_key):
        items = groups[category]
        items.sort(
            key=lambda x: (
                x.result_time is None,
                x.result_time or timedelta.max,
            )
        )
        rows = []
        for r in items:
            row = _row_base(r)
            swimmer = r.entry.swimmer
            row.update(
                {
                    'place': places.get(r.id),
                    'coach': str(swimmer.coach) if swimmer.coach else '',
                    'result': format_swim_time(r.result_time) or '',
                }
            )
            rows.append(row)
        categories.append({'title': str(category), 'rows': rows})

    return {'contest': contest, 'categories': categories}


def _build_start_context(contest):
    """Контекст шаблона стартового протокола.

    Результаты сгруппированы по номерам заплывов, внутри — по дорожкам.
    """
    results = _results_for(contest)

    grouped = defaultdict(list)
    for r in results:
        grouped[r.race_number].append(r)

    races = []
    for race_number in sorted(grouped, key=lambda x: (x is None, x)):
        items = grouped[race_number]
        items.sort(key=lambda x: x.path_number or '')
        rows = []
        for r in items:
            row = _row_base(r)
            row.update(
                {
                    'path': r.path_number or '',
                    'category': (
                        str(r.entry.category) if r.entry.category else ''
                    ),
                }
            )
            rows.append(row)
        races.append({'race_number': race_number, 'rows': rows})

    return {'contest': contest, 'races': races}


def _html_to_pdf(html: str) -> bytes:
    _ensure_font_registered()
    buffer = BytesIO()
    status = pisa.CreatePDF(html, dest=buffer, encoding='utf-8')
    if status.err:
        raise RuntimeError('Не удалось сгенерировать PDF-протокол.')
    return buffer.getvalue()


def render_final_protocol_pdf(contest) -> bytes:
    """Возвращает PDF итогового протокола соревнования."""
    html = render_to_string(
        'protocols/final_protocol.html', _build_final_context(contest)
    )
    return _html_to_pdf(html)


def render_start_protocol_pdf(contest) -> bytes:
    """Возвращает PDF стартового протокола соревнования."""
    html = render_to_string(
        'protocols/start_protocol.html', _build_start_context(contest)
    )
    return _html_to_pdf(html)
