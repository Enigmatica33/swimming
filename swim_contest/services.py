from collections import defaultdict

from django.db.models import F

from .constants import AGES
from .models import Category, Contest, Entry, Result

LANE_ORDER = ['2', '3', '1', '4']

# Дистанция определяется по возрастной группе (ключ — нижняя граница группы).
AGE_TO_DISTANCE = {
    3: 12,  # 3-4 года
    5: 25,  # 5-6 лет
    7: 50,  # 7-8 лет
    9: 50,  # 9-10 лет
    11: 50,  # 11-12 лет
    13: 100,  # 13-14 лет
    15: 100,  # 15-24 года
    25: 100,  # 25+
}


def resolve_age_group(age):
    """Возвращает возрастную группу (нижнюю границу) для возраста."""
    if age is None:
        return None
    for age_limit, _ in sorted(AGES, key=lambda x: x[0], reverse=True):
        if age >= age_limit:
            return age_limit
    return None


def resolve_distance_for(age):
    """Определяет дистанцию от возраста по правилу AGE_TO_DISTANCE."""
    group = resolve_age_group(age)
    if group is None:
        return None
    return AGE_TO_DISTANCE.get(group)


def _is_male(sex):
    """Определяет биологический пол ('male' или значения вида '1_...')."""
    s = str(sex)
    return s == 'male' or s.startswith('1')


def resolve_gender(sex, age):
    """Возвращает категорийный пол (мальчики/юноши/мужчины) по возрасту."""
    group = resolve_age_group(age)
    if group is None:
        return None
    male = _is_male(sex)
    if group <= 13:  # 3-14 лет -> мальчики/девочки
        return '1_boys' if male else '0_girls'
    if group <= 15:  # 15-24 года -> юноши/девушки
        return '1_young_men' if male else '0_young_women'
    return '1_men' if male else '0_women'  # 25+ -> мужчины/женщины


def resolve_category_for(sex, distance, age):
    """Подбирает существующую категорию по полу, дистанции и возрасту."""
    group = resolve_age_group(age)
    gender = resolve_gender(sex, age)
    if gender is None or not distance:
        return None
    return Category.objects.filter(gender=gender, distance=distance, age_group=group).first()


def get_active_contest():
    """Возвращает последнее (самое свежее) соревнование."""
    return Contest.objects.order_by('-date', '-id').first()


def distribute_races_for_contest(contest):
    Result.objects.filter(entry__contest=contest).delete()

    entries = (
        Entry.objects.filter(contest=contest, is_approved=True)
        .select_related('category', 'swimmer')
        .order_by(
            'category_id',
            F('stated_time').asc(nulls_last=True),
            'id',
        )
    )

    if not entries.exists():
        return {}

    grouped = defaultdict(list)
    for entry in entries:
        grouped[entry.category_id].append(entry)

    created_by_category = {}
    race_number = 1

    for category_id, category_entries in grouped.items():
        created_by_category[category_id] = 0

        for i in range(0, len(category_entries), 4):
            batch = category_entries[i : i + 4]

            for lane_index, entry in enumerate(batch):
                Result.objects.create(
                    entry=entry,
                    race_number=race_number,
                    path_number=LANE_ORDER[lane_index],
                )

            created_by_category[category_id] += 1
            race_number += 1

    return created_by_category
