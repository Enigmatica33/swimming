from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from .constants import (
    AGES,
    DEFAULT_SWIMSTYLE,
    DISTANCES,
    GENDERS,
    MAX_RACE_NUMBER,
    MIN_RACE_NUMBER,
    PATHS,
)


class Club(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название клуба')
    city = models.CharField(max_length=50, verbose_name='Город', blank=True, null=True)

    class Meta:
        verbose_name = 'Клуб'
        verbose_name_plural = 'Клубы'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Coach(models.Model):
    first_name = models.CharField(max_length=50, verbose_name='Имя')
    last_name = models.CharField(max_length=50, verbose_name='Фамилия')
    club = models.ForeignKey(
        Club,
        on_delete=models.SET_NULL,
        related_name='coaches',
        verbose_name='Клуб',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Тренер'
        verbose_name_plural = 'Тренеры'

    def __str__(self):
        return f'{self.last_name} {self.first_name}'


class Category(models.Model):
    gender = models.CharField(max_length=20, choices=GENDERS, verbose_name='Пол')
    distance = models.PositiveIntegerField(choices=DISTANCES, verbose_name='Дистанция')
    age_group = models.PositiveIntegerField(choices=AGES, verbose_name='Возрастная группа')

    class Meta:
        unique_together = ('gender', 'distance', 'age_group')
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ('distance', 'gender', 'age_group')

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
    date_of_birth = models.DateField(
        verbose_name='Дата рождения',
        null=True,
        blank=True,
    )
    gender = models.CharField(max_length=20, choices=GENDERS, verbose_name='Пол')
    coach = models.ForeignKey(
        Coach, on_delete=models.SET_NULL, null=True, blank=True, related_name='swimmers'
    )
    club = models.ForeignKey(
        Club,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='swimmers',
        verbose_name='Клуб',
    )

    class Meta:
        verbose_name = 'Участник'
        verbose_name_plural = 'Участники'
        ordering = ('last_name', 'first_name')

    def get_age(self, reference_date=None):
        """
        Вычисляет точный возраст, если есть дата рождения.
        Если даты рождения нет, возвращает None
        (тогда возраст возьмется из Entry).
        """
        if not self.date_of_birth:
            return None

        if not reference_date:
            reference_date = timezone.now().date()

        dob = self.date_of_birth
        return (
            reference_date.year
            - dob.year
            - ((reference_date.month, reference_date.day) < (dob.month, dob.day))
        )

    def __str__(self):
        return f'{self.last_name} {self.first_name}'


class Contest(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    date = models.DateField(verbose_name='Дата проведения')

    class Meta:
        verbose_name = 'Соревнование'
        verbose_name_plural = 'Соревнования'
        ordering = ('-date', 'name')

    def __str__(self):
        return self.name


class Entry(models.Model):
    """Заявка на участие"""

    swimmer = models.ForeignKey(
        Swimmer, on_delete=models.CASCADE, related_name='entries', verbose_name='Участник'
    )
    manual_age = models.PositiveSmallIntegerField(
        verbose_name='Возраст (если нет даты рожд.)',
        null=True,
        blank=True,
        help_text='Заполнится автоматически из даты рождения, если она указана',
    )
    contest = models.ForeignKey(
        Contest, on_delete=models.CASCADE, related_name='entries', verbose_name='Соревнование'
    )
    distance = models.PositiveIntegerField(
        choices=DISTANCES,
        verbose_name='Дистанция',
        help_text='Выберите дистанцию для автоподбора категории',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='entries',
        verbose_name='Категория',
        null=True,
        blank=True,
    )
    swimstyle = models.ForeignKey(
        Swimstyle, on_delete=models.PROTECT, verbose_name='Стиль', null=True, blank=True
    )
    stated_time = models.DurationField(null=True, blank=True, verbose_name='Заявочное время')
    is_approved = models.BooleanField(default=False, verbose_name='Одобрена')

    class Meta:
        unique_together = ('swimmer', 'contest', 'category')
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'

    def __str__(self):
        return f'Заявка № {self.id}'

    def determine_age(self):
        """Определяет, какой возраст использовать для подбора категории."""
        # 1. Сначала пробуем посчитать по дате рождения на день соревнований
        swimmer_age = self.swimmer.get_age(reference_date=self.contest.date)
        if swimmer_age is not None:
            return swimmer_age

        # 2. Если даты рождения нет, берем ручной ввод из этой заявки
        return self.manual_age

    def determine_category(self):
        # Перед сохранением пытаемся определить возраст и категорию
        current_age = self.determine_age()
        if current_age is not None:
            # Синхронизируем manual_age для красоты (если считали по DOB)
            if not self.manual_age:
                self.manual_age = current_age
            # Ищем категорию
            from .constants import AGES

            assigned_group = None
            for age_limit, _ in sorted(AGES, key=lambda x: x[0], reverse=True):
                if current_age >= age_limit:
                    assigned_group = age_limit
                    break
        if assigned_group is None:
            return None

        return Category.objects.filter(
            gender=self.swimmer.gender,
            distance=self.distance,
            age_group=assigned_group,
        ).first()

    def save(self, *args, **kwargs):
        if self.swimstyle is None:
            self.swimstyle = Swimstyle.objects.get_or_create(
                name=DEFAULT_SWIMSTYLE,
            )[0]

        if self.category is None:
            self.category = self.determine_category()

        super().save(*args, **kwargs)


class Result(models.Model):
    """Результат заплыва (создается на основе одобренной заявки)."""

    entry = models.OneToOneField(
        Entry, on_delete=models.CASCADE, related_name='result', verbose_name='Заявка'
    )
    result_time = models.DurationField(null=True, blank=True, verbose_name='Результат')
    path_number = models.CharField(max_length=1, choices=PATHS, null=True, blank=True)
    race_number = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_RACE_NUMBER), MaxValueValidator(MAX_RACE_NUMBER)],
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Результат'
        verbose_name_plural = 'Результаты'
