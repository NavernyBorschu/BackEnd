"""
Моделі даних для додатку Core.

Тут визначені основні моделі предметної області:
- PlaceType (довідник типів закладів)
- Place (заклади харчування)
- Borsch (борщі як страви)
- UserProfile (профілі користувачів)
- Review (відгуки з оцінками)
- FavoriteBorsch (обрані борщі користувачів)

Всі моделі нормалізовані та мають зв'язки ForeignKey/ManyToMany.
"""

import uuid
from django.db import models
from django.contrib.auth.models import User


# =============================================================================
# PlaceType — довідник типів закладів
# =============================================================================

class PlaceType(models.Model):
    """
    Довідковий класифікатор типів закладів.
    
    Використовується для валідації поля Place.type.
    Приклади: Ресторан, Кафе, Бістро, Паб.
    """
    
    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Код типу',
        help_text='Машинозчитуваний код (наприклад, RESTAURANT, CAFE)'
    )
    label = models.CharField(
        max_length=100,
        verbose_name='Назва типу',
        help_text='Відображувана назва українською (наприклад, "Ресторан")'
    )
    
    class Meta:
        """Мета-налаштування моделі PlaceType."""
        verbose_name = 'Тип закладу'
        verbose_name_plural = 'Типи закладів'
        ordering = ['label']
        indexes = [
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return self.label


# =============================================================================
# Place — заклади харчування (ресторани, кафе тощо)
# =============================================================================

class Place(models.Model):
    """
    Заклад харчування, де подають борщ.
    
    Містить основну інформацію: назва, адреса, координати,
    тип закладу. Має зв'язок один-до-багатьох з Borsch.
    """
    
    # Унікальний ідентифікатор (UUID для сумісності з фронтендом)
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='ID закладу'
    )
    
    # Основна інформація про заклад
    name = models.CharField(
        max_length=255,
        verbose_name='Назва закладу',
        help_text='Повна назва закладу (наприклад, "Пузата Хата")'
    )
    address = models.CharField(
        max_length=255,
        verbose_name='Адреса',
        help_text='Текстова адреса (наприклад, "Хрещатик, 25")'
    )
    
    # Координати для відображення на мапі
    # Зберігаємо як окремі поля для зручності фільтрації
    location_lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name='Широта',
        help_text='Географічна широта (від -90 до 90)'
    )
    location_lng = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name='Довгота',
        help_text='Географічна довгота (від -180 до 180)'
    )
    
    # Географічне розташування
    country = models.CharField(
        max_length=100,
        verbose_name='Країна',
        help_text='Назва країни (наприклад, "Україна")'
    )
    city = models.CharField(
        max_length=100,
        verbose_name='Місто',
        help_text='Назва міста (наприклад, "Київ")'
    )
    
    # Тип закладу (посилання на довідник)
    type = models.ForeignKey(
        PlaceType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='places',
        verbose_name='Тип закладу',
        help_text='Категорія закладу з довідника'
    )
    
    # Системні поля для відстеження змін
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата створення'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата оновлення'
    )
    
    class Meta:
        """Мета-налаштування моделі Place."""
        verbose_name = 'Заклад'
        verbose_name_plural = 'Заклади'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['city']),
            models.Index(fields=['country']),
            models.Index(fields=['location_lat', 'location_lng']),
        ]
    
    def __str__(self):
        return f'{self.name} ({self.city})'


# =============================================================================
# Borsch — борщі як страви у закладах
# =============================================================================

class Borsch(models.Model):
    """
    Конкретний борщ (страва) у певному закладі.
    
    Містить інформацію про назву, тип м'яса, ціну, вагу,
    фото та агреговані оцінки. Кожен борщ належить одному
    закладу (Place) і може мати багато відгуків (Review).
    """
    
    # Унікальний ідентифікатор (UUID для сумісності)
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='ID борщу'
    )
    
    # Зв'язок із закладом (один заклад — багато борщів)
    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name='borsches',
        verbose_name='Заклад',
        help_text='Заклад, де подається цей борщ'
    )
    
    # Основна інформація про страву
    name = models.CharField(
        max_length=255,
        verbose_name='Назва борщу',
        help_text='Назва страви (наприклад, "Борщ з пампушками")'
    )
    
    # Тип м'яса (вибір з фіксованого переліку)
    TYPE_MEAT_CHOICES = [
        ('no_meat', "Без м'яса"),
        ('chicken', 'Курка'),
        ('pork', 'Свинина'),
        ('beef', 'Яловичина'),
        ('other', 'Інше'),
    ]
    type_meat = models.CharField(
        max_length=20,
        choices=TYPE_MEAT_CHOICES,
        default='other',
        verbose_name='Тип м\'яса',
        help_text='Категорія м\'яса у борщі'
    )
    
    # Ціна та вага (нормалізовані числові значення)
    price_uah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Ціна (грн)',
        help_text='Вартість порції у гривнях (без символів ₴, ≈)'
    )
    weight_grams = models.IntegerField(
        verbose_name='Вага (г)',
        help_text='Вага порції у грамах (ціле число)'
    )
    
    # Фотографії борщу
    # Тут буде збереження фото — поки що базовий ImageField
    photo_urls = models.JSONField(
        default=list,
        blank=True,
        verbose_name='URL фотографій',
        help_text='Список URL або шляхів до зображень борщу'
    )
    
    # Агреговані оцінки (середні значення по всіх відгуках)
    # Зберігаються для швидкого доступу без перерахунку
    rating_salt = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0.0,
        verbose_name='Оцінка: солоність',
        help_text='Середня оцінка солоності (0-10)'
    )
    rating_meat = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0.0,
        verbose_name='Оцінка: м\'ясо',
        help_text='Середня оцінка якості м\'яса (0-10)'
    )
    rating_beet = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0.0,
        verbose_name='Оцінка: буряк',
        help_text='Середня оцінка якості буряка (0-10)'
    )
    rating_density = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0.0,
        verbose_name='Оцінка: густота',
        help_text='Середня оцінка густоти (0-10)'
    )
    rating_aftertaste = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0.0,
        verbose_name='Оцінка: післясмак',
        help_text='Середня оцінка післясмаку (0-10)'
    )
    rating_serving = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0.0,
        verbose_name='Оцінка: подача',
        help_text='Середня оцінка подачі (0-10)'
    )
    overall_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=0.0,
        verbose_name='Загальна оцінка',
        help_text='Середня загальна оцінка (0-10)'
    )
    
    # Системні поля для відстеження змін
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата створення'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата оновлення'
    )
    
    class Meta:
        """Мета-налаштування моделі Borsch."""
        verbose_name = 'Борщ'
        verbose_name_plural = 'Борщі'
        ordering = ['-overall_rating', 'name']
        indexes = [
            models.Index(fields=['place', 'name']),
            models.Index(fields=['type_meat']),
            models.Index(fields=['price_uah']),
            models.Index(fields=['overall_rating']),
        ]
    
    def __str__(self):
        return f'{self.name} ({self.place.name})'


# =============================================================================
# UserProfile — профілі користувачів
# =============================================================================

class UserProfile(models.Model):
    """
    Профіль користувача на основі Google OAuth.
    
    Розширює стандартну модель User додатковими полями:
    аватар, країна, локаль. Використовується для відгуків
    та персоналізації.
    """
    
    # Зв'язок зі стандартною моделлю користувача Django
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Користувач',
        help_text='Пов\'язаний обліковий запис Django User'
    )
    
    # Google OAuth ідентифікатор (sub з Google token)
    google_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        verbose_name='Google ID',
        help_text='Унікальний ідентифікатор з Google OAuth (sub)'
    )
    
    # Основна інформація з Google профілю
    given_name = models.CharField(
        max_length=100,
        verbose_name='Ім\'я',
        help_text='Ім\'я з Google профілю'
    )
    surname = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Прізвище',
        help_text='Прізвище з Google профілю'
    )
    
    # Додаткові поля профілю
    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Країна',
        help_text='Країна проживання (редагується користувачем)'
    )
    locale = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Локаль',
        help_text='Мова/регіон з Google профілю (наприклад, uk-UA)'
    )
    
    # Аватар (фото профілю)
    # Тут буде збереження фото — поки що базовий ImageField
    avatar_url = models.URLField(
        blank=True,
        verbose_name='URL аватара',
        help_text='Посилання на фото профілю (Google picture або завантажене)'
    )
    
    # Системні поля для відстеження змін
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата створення'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата оновлення'
    )
    
    class Meta:
        """Мета-налаштування моделі UserProfile."""
        verbose_name = 'Профіль користувача'
        verbose_name_plural = 'Профілі користувачів'
        ordering = ['given_name', 'surname']
        indexes = [
            models.Index(fields=['google_id']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        full_name = f'{self.given_name} {self.surname}'.strip()
        return full_name or self.user.email


# =============================================================================
# Review — відгуки з оцінками борщу
# =============================================================================

class Review(models.Model):
    """
    Відгук користувача про борщ з детальними оцінками.
    
    Містить текстовий коментар та оцінки по 6 критеріях
    плюс загальну оцінку. Кожен відгук належить одному
    борщу (Borsch) і одному користувачу (UserProfile).
    """
    
    # Унікальний ідентифікатор (UUID)
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='ID відгуку'
    )
    
    # Зв'язок з борщем (один борщ — багато відгуків)
    borsch = models.ForeignKey(
        Borsch,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Борщ',
        help_text='Борщ, до якого належить відгук'
    )
    
    # Зв'язок з користувачем (один користувач — багато відгуків)
    # Допускаємо null для тимчасових/анонімних користувачів
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        null=True,
        blank=True,
        verbose_name='Користувач',
        help_text='Автор відгуку (може бути null для тимчасових користувачів)'
    )
    
    # Тимчасовий ID для анонімних користувачів (якщо немає реального User)
    temp_user_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Тимчасовий ID',
        help_text='ID для тимчасових користувачів (temp_user_...)'
    )
    
    # Текст відгуку
    message = models.TextField(
        verbose_name='Текст відгуку',
        help_text='Коментар користувача про борщ'
    )
    
    # Оцінки по критеріях (діапазон 0-10)
    # Всі оцінки обов'язкові згідно з логікою фронтенду
    rating_salt = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        verbose_name='Солоність',
        help_text='Оцінка солоності (0-10)'
    )
    rating_meat = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        verbose_name='М\'ясо',
        help_text='Оцінка якості м\'яса (0-10)'
    )
    rating_beet = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        verbose_name='Буряк',
        help_text='Оцінка якості буряка (0-10)'
    )
    rating_density = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        verbose_name='Густота',
        help_text='Оцінка густоти (0-10)'
    )
    rating_aftertaste = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        verbose_name='Післясмак',
        help_text='Оцінка післясмаку (0-10)'
    )
    rating_serving = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        verbose_name='Подача',
        help_text='Оцінка подачі (0-10)'
    )
    overall_rating = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        verbose_name='Загальна оцінка',
        help_text='Загальна оцінка борщу (0-10)'
    )
    
    # Системні поля для відстеження змін
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата створення'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        null=True,
        verbose_name='Дата оновлення'
    )
    
    class Meta:
        """Мета-налаштування моделі Review."""
        verbose_name = 'Відгук'
        verbose_name_plural = 'Відгуки'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['borsch', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]
    
    def __str__(self):
        author = self.user.username if self.user else self.temp_user_id
        return f'Відгук від {author} на {self.borsch.name}'


# =============================================================================
# FavoriteBorsch — обрані борщі користувачів
# =============================================================================

class FavoriteBorsch(models.Model):
    """
    Список обраних борщів користувача.
    
    Зв'язок many-to-many між UserProfile та Borsch.
    Дозволяє користувачам зберігати улюблені борщі.
    """
    
    # Унікальний ідентифікатор запису
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='ID запису'
    )
    
    # Зв'язок з користувачем
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorite_borsches',
        verbose_name='Користувач',
        help_text='Користувач, який додав борщ до обраних'
    )
    
    # Зв'язок з борщем
    borsch = models.ForeignKey(
        Borsch,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Борщ',
        help_text='Борщ, доданий до обраних'
    )
    
    # Дата додавання до обраних
    added_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата додавання'
    )
    
    class Meta:
        """Мета-налаштування моделі FavoriteBorsch."""
        verbose_name = 'Обраний борщ'
        verbose_name_plural = 'Обрані борщі'
        unique_together = [['user', 'borsch']]  # Унікальна пара користувач-борщ
        ordering = ['-added_at']
        indexes = [
            models.Index(fields=['user', '-added_at']),
            models.Index(fields=['borsch']),
        ]
    
    def __str__(self):
        return f'{self.user.username} — {self.borsch.name}'
