from django.db import IntegrityError
from rest_framework import serializers

from swim_contest.models import (
    Category,
    Club,
    Coach,
    Contest,
    Entry,
    Result,
    Swimmer,
    Swimstyle,
)
from swim_contest.services import (
    get_active_contest,
    resolve_distance_for,
)


def _obj_str(obj):
    """Безопасный __str__: для None вернёт None."""
    return str(obj) if obj is not None else None


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


class ClubSerializer(serializers.ModelSerializer):
    """Сериализатор клуба."""

    class Meta:
        model = Club
        fields = ('id', 'name', 'city')


class CoachSerializer(serializers.ModelSerializer):
    """Сериализатор тренера."""

    club_name = serializers.CharField(source='club.name', read_only=True)

    class Meta:
        model = Coach
        fields = ('id', 'first_name', 'last_name', 'club', 'club_name')


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор категории."""

    gender_display = serializers.CharField(
        source='get_gender_display', read_only=True
    )
    distance_display = serializers.CharField(
        source='get_distance_display', read_only=True
    )
    age_group_display = serializers.CharField(
        source='get_age_group_display', read_only=True
    )

    class Meta:
        model = Category
        fields = (
            'id',
            'gender',
            'gender_display',
            'distance',
            'distance_display',
            'age_group',
            'age_group_display',
        )


class SwimstyleSerializer(serializers.ModelSerializer):
    """Сериализатор стиля плавания."""

    class Meta:
        model = Swimstyle
        fields = ('id', 'name')


class SwimmerSerializer(serializers.ModelSerializer):
    """Сериализатор участника."""

    club_name = serializers.CharField(source='club.name', read_only=True)
    coach_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    class Meta:
        model = Swimmer
        fields = (
            'id',
            'first_name',
            'last_name',
            'date_of_birth',
            'gender',
            'coach',
            'coach_name',
            'club',
            'club_name',
            'age',
        )

    def get_coach_name(self, obj) -> str | None:
        return str(obj.coach) if obj.coach else None

    def get_age(self, obj) -> int | None:
        return obj.get_age()


class ContestSerializer(serializers.ModelSerializer):
    """Сериализатор соревнования."""

    entries_count = serializers.IntegerField(
        source='entries.count', read_only=True
    )

    class Meta:
        model = Contest
        fields = ('id', 'name', 'date', 'entries_count')


class EntrySerializer(serializers.ModelSerializer):
    """Сериализатор заявки на участие."""

    swimmer_name = serializers.SerializerMethodField()
    contest_name = serializers.CharField(source='contest.name', read_only=True)
    category_title = serializers.SerializerMethodField()
    swimstyle_name = serializers.CharField(
        source='swimstyle.name', read_only=True
    )
    age = serializers.SerializerMethodField()
    stated_time_display = serializers.SerializerMethodField()

    class Meta:
        model = Entry
        fields = (
            'id',
            'swimmer',
            'swimmer_name',
            'manual_age',
            'age',
            'contest',
            'contest_name',
            'distance',
            'category',
            'category_title',
            'swimstyle',
            'swimstyle_name',
            'stated_time',
            'stated_time_display',
            'is_approved',
        )

    def get_age(self, obj) -> int | None:
        return obj.determine_age()

    def get_stated_time_display(self, obj):
        return format_swim_time(obj.stated_time)

    def get_swimmer_name(self, obj):
        return _obj_str(obj.swimmer)

    def get_category_title(self, obj):
        return _obj_str(obj.category)


class SwimmerInlineSerializer(serializers.ModelSerializer):
    """Вложенный сериализатор пловца (для создания заявки).

    Пловец ищется по имени и фамилии (и полу); если найден —
    используется существующий, иначе создаётся новый.
    """

    class Meta:
        model = Swimmer
        fields = (
            'first_name',
            'last_name',
            'gender',
            'date_of_birth',
            'coach',
            'club',
        )
        extra_kwargs = {
            'date_of_birth': {'required': False},
            'coach': {'required': False},
            'club': {'required': False},
        }


class EntryCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания заявки со вложенным пловцом.

    Категория и стиль определяются автоматически моделью при сохранении
    (через Entry.save/determine_category). Возраст можно передать
    напрямую (manual_age) — если у пловца нет даты рождения.
    """

    swimmer = SwimmerInlineSerializer()
    manual_age = serializers.IntegerField(
        required=False, allow_null=True, min_value=3, max_value=100
    )
    category_title = serializers.SerializerMethodField()
    swimstyle_name = serializers.SerializerMethodField()
    stated_time_display = serializers.SerializerMethodField()

    def get_category_title(self, obj):
        return str(obj.category) if obj.category else None

    def get_swimstyle_name(self, obj):
        return obj.swimstyle.name if obj.swimstyle else None

    def get_stated_time_display(self, obj):
        return format_swim_time(obj.stated_time)

    class Meta:
        model = Entry
        fields = (
            'id',
            'swimmer',
            'manual_age',
            'swimstyle',
            'stated_time',
            'stated_time_display',
            'is_approved',
            'category',
            'category_title',
            'swimstyle_name',
        )
        read_only_fields = ('category',)

    def create(self, validated_data):
        swimmer_data = validated_data.pop('swimmer')
        first_name = swimmer_data['first_name'].strip()
        last_name = swimmer_data['last_name'].strip()
        gender = swimmer_data['gender']
        dob = swimmer_data.get('date_of_birth')
        coach = swimmer_data.get('coach')
        club = swimmer_data.get('club')

        # Ищем существующего пловца по ФИ и полу, чтобы не создавать дубль
        swimmer = Swimmer.objects.filter(
            first_name=first_name, last_name=last_name, gender=gender
        ).first()

        if swimmer:
            # Дополняем дату рождения, если её ещё нет
            if dob and not swimmer.date_of_birth:
                swimmer.date_of_birth = dob
                swimmer.save(update_fields=['date_of_birth'])
        else:
            swimmer = Swimmer.objects.create(
                first_name=first_name,
                last_name=last_name,
                gender=gender,
                date_of_birth=dob or None,
                coach=coach if coach else None,
                club=club if club else None,
            )

        manual_age = validated_data.pop('manual_age', None)

        # Соревнование — активное (последнее)
        contest = get_active_contest()
        if contest is None:
            raise serializers.ValidationError(
                {'contest': 'Нет доступных соревнований.'}
            )

        # Дистанция определяется от возраста
        tmp = Entry(swimmer=swimmer, contest=contest)
        tmp.manual_age = manual_age
        age = tmp.determine_age()
        distance = resolve_distance_for(age)
        if not distance:
            raise serializers.ValidationError(
                {'distance': 'Не удалось определить дистанцию.'}
            )

        if manual_age:
            validated_data['manual_age'] = manual_age

        # Entry.save() сам определит категорию и стиль.
        # Если заявка уже подана — сообщаем об этом, а не создаём дубль.
        if Entry.objects.filter(swimmer=swimmer, contest=contest).exists():
            raise serializers.ValidationError(
                'Вы уже подали заявку на это соревнование.'
            )
        try:
            entry = Entry.objects.create(
                swimmer=swimmer,
                contest=contest,
                distance=distance,
                **validated_data,
            )
        except IntegrityError as exc:
            raise serializers.ValidationError(
                'Вы уже подали заявку на это соревнование.'
            ) from exc
        return entry


class ResultSerializer(serializers.ModelSerializer):
    """Сериализатор результата заплыва."""

    swimmer_name = serializers.SerializerMethodField()
    contest = serializers.IntegerField(
        source='entry.contest_id', read_only=True
    )
    contest_name = serializers.CharField(
        source='entry.contest.name', read_only=True
    )
    contest_date = serializers.DateField(
        source='entry.contest.date', read_only=True
    )
    category_title = serializers.SerializerMethodField()
    swimstyle_name = serializers.CharField(
        source='entry.swimstyle.name', read_only=True
    )
    result_time_display = serializers.SerializerMethodField()

    class Meta:
        model = Result
        fields = (
            'id',
            'entry',
            'swimmer_name',
            'contest',
            'contest_name',
            'contest_date',
            'category_title',
            'swimstyle_name',
            'result_time',
            'result_time_display',
            'path_number',
            'race_number',
        )

    def get_swimmer_name(self, obj):
        return _obj_str(obj.entry.swimmer)

    def get_category_title(self, obj):
        return _obj_str(obj.entry.category)

    def get_result_time_display(self, obj):
        return format_swim_time(obj.result_time)
