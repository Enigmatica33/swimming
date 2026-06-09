from django.contrib import admin
from .models import (
    Coach,
    Category,
    Club,
    Swimstyle,
    Swimmer,
    Contest,
    Entry,
    Result
)


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
        'club'
    )
    list_filter = ('gender', 'coach', 'club')
    search_fields = (
        'last_name',
        'first_name',
        'coach__last_name',
        'club__name'
    )
    autocomplete_fields = ('coach', 'club')

    @admin.display(description='Возраст')
    def display_age(self, obj):
        return obj.get_age()


@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = ('name', 'date')
    search_fields = ('name',)
    list_filter = ('date',)


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = (
        'swimmer',
        'contest',
        'category',
        'swimstyle',
        'is_approved'
    )
    list_filter = ('contest', 'category', 'swimstyle', 'is_approved')
    search_fields = ('swimmer__last_name', 'contest__name')
    autocomplete_fields = ('swimmer', 'contest', 'category', 'swimstyle')
    actions = ['approve_entries']

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
        'result_time'
    )
    list_filter = ('entry__contest', 'entry__category')
    search_fields = ('entry__swimmer__last_name', 'entry__swimmer__first_name')
    autocomplete_fields = ('entry',)

    @admin.display(description='Пловец')
    def get_swimmer(self, obj):
        return obj.entry.swimmer

    @admin.display(description='Соревнование')
    def get_contest(self, obj):
        return obj.entry.contest
