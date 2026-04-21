"""
Маршрутизація URL для API додатку Core.

Цей файл налаштовує Django REST Framework Router та реєструє
всі ViewSets для автоматичної генерації URL patterns.

Основні ендпоінти:
- /api/places/ - заклади
- /api/borsches/ - борщі
- /api/reviews/ - відгуки
- /api/profile/ - профілі користувачів
- /api/favorites/ - обрані борщі
- /api/place-types/ - типи закладів
- /api/users/ - користувачі
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views_auth import GoogleAuthView
from .viewsets import (
    PlaceTypeViewSet,
    PlaceViewSet,
    BorschViewSet,
    UserProfileViewSet,
    ReviewViewSet,
    FavoriteBorschViewSet,
    UserViewSet,
)


# Створення роутера для автоматичної реєстрації ViewSets
router = DefaultRouter()

# Реєстрація ViewSets
# Формат URL: /api/{basename}/
router.register(r'place-types', PlaceTypeViewSet, basename='place-type')
router.register(r'places', PlaceViewSet, basename='place')
router.register(r'borsches', BorschViewSet, basename='borsch')
router.register(r'profile', UserProfileViewSet, basename='profile')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'favorites', FavoriteBorschViewSet, basename='favorite')
router.register(r'users', UserViewSet, basename='user')


# URL patterns для API
urlpatterns = [
    path('auth/google/', GoogleAuthView.as_view(), name='auth-google'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    # Всі маршрути від роутера
    path('', include(router.urls)),
]
