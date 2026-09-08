from django.contrib import admin, messages
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse

from .forms import ResultFormSet
from .models import (
    Category,
    Club,
    Coach,
    Contest,
    Entry,
    Result,
    Swimmer,
    Swimstyle,
)
from .services import distribute_races_for_contest


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('name', 'city')
    search_fields = ('name',)


@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'club')
    list_filter = ('club',)
    search_fields = ('last_name', 'first_name', 'club__name')
    autocomplete_fields = ('club',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('distance', 'gender', 'age_group')
    list_filter = ('distance', 'gender', 'age_group')
    search_fields = ('distance',)


@admin.register(Swimstyle)
class SwimstyleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Swimmer)
class SwimmerAdmin(admin.ModelAdmin):
    list_display = (
        'last_name',
        'first_name',
        'gender',
        'display_age',
        'coach',
        'club',
    )
    list_filter = ('gender', 'coach', 'club')
    search_fields = (
        'last_name',
        'first_name',
        'coach__last_name',
        'club__name',
    )
    autocomplete_fields = ('coach', 'club')

    @admin.display(description='Возраст')
    def display_age(self, obj):
        return obj.get_age()


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = ('name', 'date')
    search_fields = ('name',)
    change_form_template = 'admin/swim_contest/contest/change_form.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/results/',
                self.admin_site.admin_view(self.results_view),
                name='swim_contest_contest_results',
            ),
            path(
                '<path:object_id>/generate-races/',
                self.admin_site.admin_view(self.generate_races),
                name='swim_contest_contest_generate_races',
            ),
        ]
        return custom_urls + urls

    def results_view(self, request, object_id):
        contest = get_object_or_404(Contest, pk=object_id)

        # Получаем все уникальные номера заплывов для пагинации
        all_race_numbers = (
            Result.objects.filter(entry__contest=contest)
            .values_list('race_number', flat=True)
            .distinct()
            .order_by('race_number')
        )

        # Пагинатор: 1 заплыв на страницу
        paginator = Paginator(all_race_numbers, 1)
        page_number = request.GET.get('p', 1)
        page_obj = paginator.get_page(page_number)

        # Получаем номер заплыва для текущей страницы
        current_race_number = (
            page_obj.object_list[0] if page_obj.object_list else None
        )

        # Фильтруем результаты только для этого заплыва
        results = (
            Result.objects.with_entry_details()
            .filter(entry__contest=contest, race_number=current_race_number)
            .order_by('path_number')
        )

        if request.method == 'POST':
            formset = ResultFormSet(request.POST, queryset=results)
            if formset.is_valid():
                formset.save()
                self.message_user(
                    request, 'Заплыв успешно обновлен.', messages.SUCCESS
                )
                # Возвращаемся на ту же страницу с пагинацией
                return HttpResponseRedirect(f'{request.path}?p={page_number}')
        else:
            formset = ResultFormSet(queryset=results)

        context = dict(
            self.admin_site.each_context(request),
            contest=contest,
            formset=formset,
            page_obj=page_obj,  # Передаем объект пагинации в шаблон
            title=(
                f'Заплыв №{current_race_number} из {paginator.count} '
                f'({contest})'
            ),
        )
        return render(
            request, 'admin/swim_contest/contest/results.html', context
        )

    def generate_races(self, request, object_id):
        contest = get_object_or_404(Contest, pk=object_id)
        result = distribute_races_for_contest(contest)
        total = sum(result.values())
        self.message_user(
            request,
            f'Сформировано заплывов: {total}',
            messages.SUCCESS,
        )
        return HttpResponseRedirect(
            reverse('admin:swim_contest_contest_results', args=[contest.pk])
        )


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = (
        'swimmer',
        'contest',
        'category',
        'swimstyle',
        'is_approved',
    )
    list_filter = ('contest', 'category', 'swimstyle', 'is_approved')
    search_fields = ('swimmer__last_name', 'contest__name')
    autocomplete_fields = ('swimmer', 'contest', 'category', 'swimstyle')
    actions = ['approve_entries']
    exclude = ('category', 'swimstyle')

    @admin.action(description='Одобрить выбранные заявки')
    def approve_entries(self, request, queryset):
        queryset.update(is_approved=True)


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = (
        'get_swimmer',
        'get_contest',
        'race_number',
        'path_number',
        'result_time',
    )
    list_filter = ('entry__contest', 'entry__category')
    search_fields = ('entry__swimmer__last_name', 'entry__swimmer__first_name')
    autocomplete_fields = ('entry',)

    @admin.display(description='Пловец')
    def get_swimmer(self, obj):
        return obj.swimmer

    @admin.display(description='Соревнование')
    def get_contest(self, obj):
        return obj.contest
