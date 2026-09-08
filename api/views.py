from collections import defaultdict
from datetime import date

from django.db.models import Count
from django.http import HttpResponse
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
from swim_contest.pdf import (
    render_final_protocol_pdf,
    render_start_protocol_pdf,
)
from swim_contest.services import (
    compute_places_from_results,
    get_active_contest,
    resolve_category_for,
    resolve_distance_for,
)
from swim_contest.utils import age_on_date

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

    queryset = Coach.objects.select_related('club').annotate(
        swimmers_count=Count('swimmers')
    )
    serializer_class = CoachSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('last_name', 'first_name', 'club__name')

    @staticmethod
    def _compute_prize_places():
        """Сколько раз пловцы каждого тренера попадали в 1–3 места.

        Место считается по всем участникам пары «соревнование + категория».
        Результаты загружаются одним запросом, а места считаются одним
        проходом для всех соревнований сразу (без N+1).
        """
        counts = defaultdict(int)
        results = list(Result.objects.with_place_details())
        coach_by_result = {r.id: r.entry.swimmer.coach_id for r in results}
        places = compute_places_from_results(results)

        for result_id, place in places.items():
            if place <= 3:
                coach_id = coach_by_result.get(result_id)
                if coach_id:
                    counts[coach_id] += 1
        return counts

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        prizes = self._compute_prize_places()

        coaches = list(queryset)
        for coach in coaches:
            coach.prize_places = prizes.get(coach.id, 0)
        coaches.sort(key=lambda c: c.prize_places, reverse=True)

        serializer = self.get_serializer(coaches, many=True)
        return Response(serializer.data)


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

    @action(detail=True, methods=['get'], url_path='history')
    def history(self, request, pk=None):
        """Карточка пловца: данные + результаты по всем соревнованиям.

        Место считается отдельно для каждой пары «соревнование + категория».
        """
        swimmer = self.get_object()
        qs = Result.objects.with_entry_details().filter(entry__swimmer=swimmer)

        # Место пловца считается по ВСЕМ участникам той же пары
        # «соревнование + категория», а не только среди его результатов.
        # Все результаты нужных соревнований грузим ОДНИМ запросом
        # и считаем места одним проходом (устраняет N+1 по соревнованиям).
        place_by_result_id = {}
        contest_ids = set(qs.values_list('entry__contest_id', flat=True))
        if contest_ids:
            all_results = Result.objects.with_place_details().filter(
                entry__contest_id__in=contest_ids
            )
            place_by_result_id = compute_places_from_results(all_results)

        # Результаты по соревнованиям (в хронологическом порядке)
        contests = defaultdict(list)
        ordered_qs = sorted(qs, key=lambda x: x.entry.contest.date)
        for r in ordered_qs:
            data = ResultSerializer(
                r, context=self.get_serializer_context()
            ).data
            data['place'] = place_by_result_id.get(r.id)
            contests[r.entry.contest_id].append(data)

        contest_list = [
            {
                'contest': cid,
                'contest_name': items[0]['contest_name'],
                'contest_date': items[0]['contest_date'],
                'results': items,
            }
            for cid, items in contests.items()
        ]

        return Response(
            {
                'id': swimmer.id,
                'first_name': swimmer.first_name,
                'last_name': swimmer.last_name,
                'date_of_birth': swimmer.date_of_birth,
                'gender': swimmer.gender,
                'club_name': str(swimmer.club) if swimmer.club else None,
                'coach_name': str(swimmer.coach) if swimmer.coach else None,
                'age': swimmer.get_age(),
                'contests': contest_list,
            }
        )


class ContestViewSet(viewsets.ModelViewSet):
    """Управление соревнованиями."""

    queryset = Contest.objects.annotate(entries_count=Count('entries'))
    serializer_class = ContestSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)

    @action(detail=True, methods=['get'], url_path='final-protocol')
    def final_protocol(self, request, pk=None):
        """Итоговый протокол соревнования в формате PDF."""
        contest = self.get_object()
        pdf = render_final_protocol_pdf(contest)
        return _pdf_response(pdf, f'итоговый-протокол-{contest.pk}.pdf')

    @action(detail=True, methods=['get'], url_path='start-protocol')
    def start_protocol(self, request, pk=None):
        """Стартовый протокол соревнования в формате PDF."""
        contest = self.get_object()
        pdf = render_start_protocol_pdf(contest)
        return _pdf_response(pdf, f'стартовый-протокол-{contest.pk}.pdf')


def _pdf_response(pdf_bytes: bytes, filename: str) -> HttpResponse:
    """HTTP-ответ с PDF и заголовком Content-Disposition."""
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


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
            reference_date = contest.date if contest else date.today()
            resolved_age = age_on_date(date_of_birth, reference_date)

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

    def get_queryset(self):
        """Фильтр по соревнованию через ?contest=<id>."""
        qs = super().get_queryset()
        contest = self.request.query_params.get('contest')
        if contest:
            qs = qs.filter(entry__contest_id=contest)
        return qs
