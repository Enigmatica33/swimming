from datetime import date

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

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
    resolve_category_for,
    resolve_distance_for,
)

from .serializers import (
    CategorySerializer,
    ClubSerializer,
    CoachSerializer,
    ContestSerializer,
    EntryCreateSerializer,
    EntrySerializer,
    ResultSerializer,
    SwimmerSerializer,
    SwimstyleSerializer,
)


class ClubViewSet(viewsets.ModelViewSet):
    """Управление клубами."""

    queryset = Club.objects.all()
    serializer_class = ClubSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name', 'city')


class CoachViewSet(viewsets.ModelViewSet):
    """Управление тренерами."""

    queryset = Coach.objects.select_related('club')
    serializer_class = CoachSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('last_name', 'first_name', 'club__name')


class CategoryViewSet(viewsets.ModelViewSet):
    """Управление категориями."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('distance',)


class SwimstyleViewSet(viewsets.ModelViewSet):
    """Управление стилями плавания."""

    queryset = Swimstyle.objects.all()
    serializer_class = SwimstyleSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


class SwimmerViewSet(viewsets.ModelViewSet):
    """Управление участниками."""

    queryset = Swimmer.objects.select_related('coach', 'club')
    serializer_class = SwimmerSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('last_name', 'first_name', 'club__name')


class ContestViewSet(viewsets.ModelViewSet):
    """Управление соревнованиями."""

    queryset = Contest.objects.all()
    serializer_class = ContestSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


def _calc_age(dob, reference_date=None):
    """Считает возраст на reference_date (по умолчанию — сегодня)."""
    if not dob:
        return None
    if isinstance(dob, str):
        dob = date.fromisoformat(dob)
    if reference_date is None:
        reference_date = date.today()
    return (
        reference_date.year
        - dob.year
        - ((reference_date.month, reference_date.day) < (dob.month, dob.day))
    )


class EntryViewSet(viewsets.ModelViewSet):
    """Управление заявками на участие."""

    queryset = Entry.objects.select_related(
        'swimmer', 'contest', 'category', 'swimstyle'
    )
    filter_backends = (filters.SearchFilter,)
    search_fields = ('swimmer__last_name', 'contest__name')

    def get_serializer_class(self):
        if self.action in ('create',):
            return EntryCreateSerializer
        return EntrySerializer

    @action(detail=False, methods=['post'], url_path='resolve-category')
    def resolve_category(self, request):
        """Определяет категорию по полу, возрасту/дате рождения."""
        sex = request.data.get('sex') or request.data.get('gender')
        distance = request.data.get('distance')
        age = request.data.get('age')
        date_of_birth = request.data.get('date_of_birth')

        if not sex:
            return Response(
                {'detail': 'Поле sex обязательно.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Возраст: явный или из даты рождения на день активного соревнования
        resolved_age = age
        if resolved_age is None and date_of_birth:
            contest = get_active_contest()
            reference_date = contest.date if contest else None
            resolved_age = _calc_age(date_of_birth, reference_date)

        # Дистанция определяется от возраста, если не передана явно
        if not distance:
            distance = resolve_distance_for(resolved_age)

        category = resolve_category_for(sex, distance, resolved_age)

        return Response(
            {
                'age': resolved_age,
                'distance': distance,
                'gender': category.gender if category else None,
                'category_id': category.id if category else None,
                'category_title': str(category) if category else None,
            }
        )


class ResultViewSet(viewsets.ModelViewSet):
    """Управление результатами заплывов."""

    queryset = Result.objects.select_related(
        'entry__swimmer',
        'entry__contest',
        'entry__category',
        'entry__swimstyle',
    )
    serializer_class = ResultSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('entry__swimmer__last_name',)
