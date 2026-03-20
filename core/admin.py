"""
Налаштування Django адмін-панелі для моделей додатку Core.

Цей файл реєструє всі моделі в адмін-панелі та налаштовує:
- list_display: поля для відображення у списку
- search_fields: поля для пошуку
- list_filter: фільтри у правій панелі
- inlines: пов'язані моделі для редагування на одній сторінці

Адмін-панель доступна за адресою: /admin/
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import PlaceType, Place, Borsch, UserProfile, Review, FavoriteBorsch


# =============================================================================
# PlaceType — адмін-панель
# =============================================================================

@admin.register(PlaceType)
class PlaceTypeAdmin(admin.ModelAdmin):
    """
    Налаштування адмін-панелі для типів закладів.
    
    Дозволяє швидко переглядати та редагувати довідник типів.
    """
    list_display = ['code', 'label']
    search_fields = ['label', 'code']
    ordering = ['label']


# =============================================================================
# Place — адмін-панель
# =============================================================================

class BorschInline(admin.TabularInline):
    """
    Вбудований список борщів для сторінки закладу.
    
    Дозволяє переглядати та редагувати борщі прямо на сторінці закладу.
    """
    model = Borsch
    extra = 0
    fields = ['name', 'type_meat', 'price_uah', 'overall_rating']
    readonly_fields = ['overall_rating']


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    """
    Налаштування адмін-панелі для закладів.
    
    Основні інструменти для управління закладами.
    """
    list_display = ['name', 'city', 'type', 'address', 'created_at']
    list_filter = ['city', 'country', 'type']
    search_fields = ['name', 'address', 'city']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [BorschInline]
    ordering = ['name']
    
    fieldsets = (
        (_('Основна інформація'), {
            'fields': ('id', 'name', 'address', 'type')
        }),
        (_('Географічне розташування'), {
            'fields': ('country', 'city', 'location_lat', 'location_lng')
        }),
        (_('Системна інформація'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# =============================================================================
# Borsch — адмін-панель
# =============================================================================

class ReviewInline(admin.TabularInline):
    """
    Вбудований список відгуків для сторінки борщу.
    
    Дозволяє переглядати відгуки про конкретний борщ.
    """
    model = Review
    extra = 0
    fields = ['user', 'message', 'overall_rating', 'created_at']
    readonly_fields = ['user', 'message', 'overall_rating', 'created_at']
    can_delete = True


@admin.register(Borsch)
class BorschAdmin(admin.ModelAdmin):
    """
    Налаштування адмін-панелі для борщів.
    
    Дозволяє управляти стравами та переглядати відгуки.
    """
    list_display = ['name', 'place', 'type_meat', 'price_uah', 'weight_grams', 'overall_rating']
    list_filter = ['type_meat', 'place']
    search_fields = ['name', 'place__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [ReviewInline]
    ordering = ['-overall_rating', 'name']
    
    fieldsets = (
        (_('Основна інформація'), {
            'fields': ('id', 'name', 'place', 'type_meat')
        }),
        (_('Характеристики'), {
            'fields': ('price_uah', 'weight_grams', 'photo_urls')
        }),
        (_('Агреговані оцінки'), {
            'fields': (
                'rating_salt', 'rating_meat', 'rating_beet',
                'rating_density', 'rating_aftertaste', 'rating_serving',
                'overall_rating'
            ),
            'description': _('Ці оцінки обчислюються автоматично на основі відгуків')
        }),
        (_('Системна інформація'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# =============================================================================
# UserProfile — адмін-панель
# =============================================================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Налаштування адмін-панелі для профілів користувачів.
    
    Дозволяє переглядати та редагувати профілі користувачів.
    """
    list_display = ['get_full_name', 'user', 'email', 'country', 'created_at']
    list_filter = ['country']
    search_fields = ['given_name', 'surname', 'user__email', 'google_id']
    readonly_fields = ['user', 'google_id', 'created_at', 'updated_at']
    ordering = ['given_name']
    
    fieldsets = (
        (_('Основна інформація'), {
            'fields': ('user', 'google_id')
        }),
        (_('Персональні дані'), {
            'fields': ('given_name', 'surname', 'country', 'locale')
        }),
        (_('Аватар'), {
            'fields': ('avatar_url',),
            'description': _('URL фото профілю з Google або завантажене зображення')
        }),
        (_('Системна інформація'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        """Повертає повне ім'я користувача."""
        full_name = f'{obj.given_name} {obj.surname}'.strip()
        return full_name or '—'
    get_full_name.short_description = _('Повне ім\'я')
    
    def email(self, obj):
        """Повертає email користувача."""
        return obj.user.email
    email.short_description = _('Email')


# =============================================================================
# Review — адмін-панель
# =============================================================================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Налаштування адмін-панелі для відгуків.
    
    Основний інструмент для модерації відгуків.
    """
    list_display = ['get_author', 'borsch', 'overall_rating', 'created_at']
    list_filter = ['borsch__place', 'created_at']
    search_fields = ['message', 'user__username', 'borsch__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Основна інформація'), {
            'fields': ('id', 'borsch', 'user', 'temp_user_id')
        }),
        (_('Відгук'), {
            'fields': ('message',)
        }),
        (_('Оцінки'), {
            'fields': (
                'rating_salt', 'rating_meat', 'rating_beet',
                'rating_density', 'rating_aftertaste', 'rating_serving',
                'overall_rating'
            )
        }),
        (_('Системна інформація'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_author(self, obj):
        """Повертає ім'я автора відгуку."""
        if obj.user:
            return obj.user.username
        return obj.temp_user_id or _('Анонім')
    get_author.short_description = _('Автор')


# =============================================================================
# FavoriteBorsch — адмін-панель
# =============================================================================

@admin.register(FavoriteBorsch)
class FavoriteBorschAdmin(admin.ModelAdmin):
    """
    Налаштування адмін-панелі для обраних борщів.
    
    Дозволяє переглядати, які користувачі додали борщі до обраних.
    """
    list_display = ['user', 'borsch', 'added_at']
    list_filter = ['added_at', 'borsch__place']
    search_fields = ['user__username', 'borsch__name']
    readonly_fields = ['id', 'added_at']
    ordering = ['-added_at']
    date_hierarchy = 'added_at'
