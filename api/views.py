from rest_framework import filters, viewsets

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

from .serializers import (
    CategorySerializer,
    ClubSerializer,
    CoachSerializer,
    ContestSerializer,
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


class EntryViewSet(viewsets.ModelViewSet):
    """Управление заявками на участие."""

    queryset = Entry.objects.select_related('swimmer', 'contest', 'category', 'swimstyle')
    serializer_class = EntrySerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('swimmer__last_name', 'contest__name')


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
