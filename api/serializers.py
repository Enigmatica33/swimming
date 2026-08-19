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

    gender_display = serializers.CharField(source='get_gender_display', read_only=True)
    distance_display = serializers.CharField(source='get_distance_display', read_only=True)
    age_group_display = serializers.CharField(source='get_age_group_display', read_only=True)

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

    entries_count = serializers.IntegerField(source='entries.count', read_only=True)

    class Meta:
        model = Contest
        fields = ('id', 'name', 'date', 'entries_count')


class EntrySerializer(serializers.ModelSerializer):
    """Сериализатор заявки на участие."""

    swimmer_name = serializers.CharField(source='swimmer.__str__', read_only=True)
    contest_name = serializers.CharField(source='contest.name', read_only=True)
    category_title = serializers.CharField(source='category.__str__', read_only=True)
    swimstyle_name = serializers.CharField(source='swimstyle.name', read_only=True)
    age = serializers.SerializerMethodField()

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
            'is_approved',
        )

    def get_age(self, obj) -> int | None:
        return obj.determine_age()


class ResultSerializer(serializers.ModelSerializer):
    """Сериализатор результата заплыва."""

    swimmer_name = serializers.CharField(source='entry.swimmer.__str__', read_only=True)
    contest = serializers.IntegerField(source='entry.contest_id', read_only=True)
    contest_name = serializers.CharField(source='entry.contest.name', read_only=True)
    category_title = serializers.CharField(source='entry.category.__str__', read_only=True)
    swimstyle_name = serializers.CharField(source='entry.swimstyle.name', read_only=True)

    class Meta:
        model = Result
        fields = (
            'id',
            'entry',
            'swimmer_name',
            'contest',
            'contest_name',
            'category_title',
            'swimstyle_name',
            'result_time',
            'path_number',
            'race_number',
        )
