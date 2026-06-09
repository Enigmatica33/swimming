from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from .constants import (
    GENDERS,
    DISTANCES,
    AGES,
    PATHS,
    MIN_RACE_NUMBER,
    MAX_RACE_NUMBER
)


class Coach(models.Model):
    first_name = models.CharField(max_length=50, verbose_name='Имя')
    last_name = models.CharField(max_length=50, verbose_name='Фамилия')
    club = models.CharField(
        max_length=100,
        verbose_name='Клуб',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Тренер'
        verbose_name_plural = 'Тренеры'

    def __str__(self):
        return f'{self.last_name} {self.first_name}'


class Category(models.Model):
    gender = models.CharField(
        max_length=20,
        choices=GENDERS,
        verbose_name='Пол'
    )
    distance = models.PositiveIntegerField(
        choices=DISTANCES,
        verbose_name='Дистанция'
    )
    age_group = models.PositiveIntegerField(
        choices=AGES,
        verbose_name='Возрастная группа'
    )

    class Meta:
        unique_together = ('gender', 'distance', 'age_group')
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return (
            f'{self.get_distance_display()} - '
            f'{self.get_gender_display()} '
            f'({self.get_age_group_display()})'
        )


class Swimstyle(models.Model):
    name = models.CharField(max_length=50, verbose_name='Стиль плавания')

    class Meta:
        verbose_name = 'Стиль плавания'
        verbose_name_plural = 'Стили плавания'

    def __str__(self):
        return self.name


class Swimmer(models.Model):
    first_name = models.CharField(max_length=50, verbose_name='Имя')
    last_name = models.CharField(max_length=50, verbose_name='Фамилия')
    date_of_birth = models.DateField(verbose_name='Дата рождения')
    gender = models.CharField(
        max_length=20,
        choices=GENDERS,
        verbose_name='Пол'
    )
    coach = models.ForeignKey(
        Coach,
        on_delete=models.SET_NULL,
        null=True,
        related_name='swimmers'
    )

    class Meta:
        verbose_name = 'Участник'
        verbose_name_plural = 'Участники'

    def get_age(self):
        today = timezone.now().date()
        return (
            today.year
            - self.date_of_birth.year
            - (
                (today.month, today.day)
                < (self.date_of_birth.month, self.date_of_birth.day)
            )
        )

    def __str__(self):
        return f'{self.last_name} {self.first_name}'


class Contest(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    date = models.DateField(verbose_name='Дата проведения')

    class Meta:
        verbose_name = 'Соревнование'
        verbose_name_plural = 'Соревнования'

    def __str__(self):
        return self.name


class Entry(models.Model):
    """Заявка на участие"""
    swimmer = models.ForeignKey(
        Swimmer,
        on_delete=models.CASCADE,
        related_name='entries'
    )
    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
        related_name='entries'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='entries'
    )
    swimstyle = models.ForeignKey(
        Swimstyle,
        on_delete=models.PROTECT,
        verbose_name='Стиль'
    )
    stated_time = models.DurationField(
        null=True,
        blank=True,
        verbose_name='Заявочное время'
    )
    is_approved = models.BooleanField(default=False, verbose_name='Одобрена')

    class Meta:
        unique_together = ('swimmer', 'contest', 'category')
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'


class Result(models.Model):
    """Результат заплыва (создается на основе одобренной заявки)"""
    entry = models.OneToOneField(
        Entry,
        on_delete=models.CASCADE,
        related_name='result'
    )
    result_time = models.DurationField(
        null=True,
        blank=True,
        verbose_name='Время'
    )
    path_number = models.CharField(
        max_length=1,
        choices=PATHS, null=True,
        blank=True
    )
    race_number = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_RACE_NUMBER),
            MaxValueValidator(MAX_RACE_NUMBER)
        ],
        null=True, blank=True
    )

    class Meta:
        verbose_name = 'Результат'
        verbose_name_plural = 'Результаты'
