from collections import defaultdict

from django.db.models import F

from .models import Entry, Result

LANE_ORDER = ['2', '3', '1', '4']


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
