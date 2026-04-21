"""
ViewSets Django REST Framework для моделей додатку Core.

Цей файл містить ViewSets для обробки HTTP-запитів:
- list: отримати список об'єктів
- retrieve: отримати один об'єкт по ID
- create: створити новий об'єкт
- update: оновити об'єкт
- destroy: видалити об'єкт

Для борщів додано extra action для завантаження фото.
"""

import os
import uuid
from django.conf import settings
from rest_framework import viewsets, status, decorators, parsers
from rest_framework.response import Response
from django.db import models

from .models import PlaceType, Place, Borsch, UserProfile, Review, FavoriteBorsch
from .serializers import (
    PlaceTypeSerializer,
    PlaceSerializer, PlaceCreateSerializer, PlaceUpdateSerializer,
    BorschSerializer, BorschCreateSerializer, BorschUpdateSerializer,
    UserProfileSerializer, UserProfileUpdateSerializer,
    ReviewSerializer, ReviewCreateSerializer, ReviewUpdateSerializer,
    FavoriteBorschSerializer,
    UserSerializer
)
from .permissions import IsAuthenticatedOrReadOnlyUA
from .pagination import CustomPageNumberPagination
from django.contrib.auth.models import User


# =============================================================================
# PlaceType ViewSet
# =============================================================================

class PlaceTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для типів закладів.
    
    Тільки читання (список та детальна інформація).
    Створення/оновлення типів відбувається через адмін-панель.
    """
    queryset = PlaceType.objects.all()
    serializer_class = PlaceTypeSerializer
    permission_classes = [IsAuthenticatedOrReadOnlyUA]
    pagination_class = CustomPageNumberPagination
    
    def get_queryset(self):
        """Отримати список типів, відсортований за назвою."""
        return PlaceType.objects.all().order_by('label')


# =============================================================================
# Place ViewSet
# =============================================================================

class PlaceViewSet(viewsets.ModelViewSet):
    """
    ViewSet для закладів.
    
    Підтримує CRUD операції:
    - GET /api/places/ - список всіх закладів
    - GET /api/places/{id}/ - детальна інформація
    - POST /api/places/ - створити заклад (потрібна авторизація)
    - PATCH /api/places/{id}/ - оновити заклад (потрібна авторизація)
    - DELETE /api/places/{id}/ - видалити заклад (потрібна авторизація)
    
    Фільтри:
    - search - пошук по назві та адресі
    - city - фільтр по місту
    - type - фільтр по типу закладу
    """
    queryset = Place.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnlyUA]
    pagination_class = CustomPageNumberPagination
    
    def get_serializer_class(self):
        """Вибір серіалізатора залежно від дії."""
        if self.action == 'create':
            return PlaceCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PlaceUpdateSerializer
        return PlaceSerializer
    
    def get_queryset(self):
        """
        Отримати список закладів з фільтрацією.
        
        Параметри запиту:
        - search: пошук по назві або адресі
        - city: фільтр по місту
        - type: фільтр по типу закладу (код типу)
        """
        queryset = Place.objects.all().order_by('name')
        
        # Пошук по назві та адресі
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) |
                models.Q(address__icontains=search)
            )
        
        # Фільтр по місту
        city = self.request.query_params.get('city', None)
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        # Фільтр по типу закладу
        place_type = self.request.query_params.get('type', None)
        if place_type:
            queryset = queryset.filter(type__code=place_type)
        
        return queryset


# =============================================================================
# Borsch ViewSet
# =============================================================================

class BorschViewSet(viewsets.ModelViewSet):
    """
    ViewSet для борщів.
    
    Підтримує CRUD операції:
    - GET /api/borsches/ - список всіх борщів
    - GET /api/borsches/{id}/ - детальна інформація
    - POST /api/borsches/ - створити борщ (потрібна авторизація)
    - PATCH /api/borsches/{id}/ - оновити борщ (потрібна авторизація)
    - DELETE /api/borsches/{id}/ - видалити борщ (потрібна авторизація)
    
    Фільтри:
    - place_id - фільтр по закладу
    - type_meat - фільтр по типу м'яса
    - min_price, max_price - фільтр по ціні
    
    Extra actions:
    - POST /api/borsches/{id}/upload_photo/ - завантажити фото борщу
    """
    queryset = Borsch.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnlyUA]
    pagination_class = CustomPageNumberPagination
    
    def get_serializer_class(self):
        """Вибір серіалізатора залежно від дії."""
        if self.action == 'create':
            return BorschCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return BorschUpdateSerializer
        return BorschSerializer
    
    def get_queryset(self):
        """
        Отримати список борщів з фільтрацією.
        
        Параметри запиту:
        - place_id: фільтр по закладу
        - type_meat: фільтр по типу м'яса
        - min_price, max_price: діапазон цін
        """
        queryset = Borsch.objects.all().order_by('-overall_rating', 'name')
        
        # Фільтр по закладу
        place_id = self.request.query_params.get('place_id', None)
        if place_id:
            queryset = queryset.filter(place_id=place_id)
        
        # Фільтр по типу м'яса
        meat_type = self.request.query_params.get('type_meat', None)
        if meat_type:
            queryset = queryset.filter(type_meat=meat_type)
        
        # Фільтр по ціні
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        if min_price:
            queryset = queryset.filter(price_uah__gte=min_price)
        if max_price:
            queryset = queryset.filter(price_uah__lte=max_price)
        
        return queryset
    
    @decorators.action(
        detail=True,
        methods=['post'],
        parser_classes=[parsers.MultiPartParser],
        url_path='upload_photo'
    )
    def upload_photo(self, request, pk=None):
        """
        Завантажити фото для борщу.
        
        Приймає multipart/form-data з полем 'photo'.
        Зберігає файл у медіа-директорію та повертає URL.
        """
        borsch = self.get_object()
        
        if 'photo' not in request.FILES:
            return Response(
                {'error': 'Файл не знайдено. Використовуйте поле "photo".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        photo_file = request.FILES['photo']
        
        # Генерація унікального імені файлу
        file_extension = os.path.splitext(photo_file.name)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        
        # Шлях для збереження (URL завжди з прямими слешами; шлях на диску — окремо)
        rel = ('borsches', str(borsch.id), 'photos')
        upload_path = '/'.join(rel)
        full_path = os.path.join(settings.MEDIA_ROOT, *rel)
        
        # Створення директорії якщо не існує
        os.makedirs(full_path, exist_ok=True)
        
        # Збереження файлу
        file_path = os.path.join(full_path, unique_filename)
        with open(file_path, 'wb+') as destination:
            for chunk in photo_file.chunks():
                destination.write(chunk)
        
        # Додавання URL до списку photo_urls
        photo_url = f"{settings.MEDIA_URL}{upload_path}/{unique_filename}"
        
        # Оновлення списку фото
        photo_urls = borsch.photo_urls or []
        photo_urls.append(photo_url)
        borsch.photo_urls = photo_urls
        borsch.save()
        
        return Response(
            {'photo_url': photo_url, 'message': 'Фото успішно завантажено'},
            status=status.HTTP_201_CREATED
        )


# =============================================================================
# UserProfile ViewSet
# =============================================================================

class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet для профілів користувачів.
    
    GET /api/profile/me/ - отримати профіль поточного користувача
    PATCH /api/profile/me/ - оновити профіль поточного користувача
    """
    queryset = UserProfile.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnlyUA]
    
    def get_serializer_class(self):
        """Вибір серіалізатора залежно від дії."""
        if self.action in ['update', 'partial_update']:
            return UserProfileUpdateSerializer
        return UserProfileSerializer
    
    @decorators.action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        """
        Отримати або оновити профіль поточного користувача.
        
        Для анонімних користувачів повертає 401.
        """
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Потрібна авторизація'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Отримання або створення профілю
        profile, created = UserProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'given_name': request.user.first_name or request.user.username,
                'surname': request.user.last_name,
            }
        )
        
        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        
        elif request.method == 'PATCH':
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )


# =============================================================================
# Review ViewSet
# =============================================================================

class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet для відгуків.
    
    Підтримує CRUD операції:
    - GET /api/borsches/{borsch_id}/reviews/ - список відгуків для борщу
    - GET /api/reviews/{id}/ - детальна інформація
    - POST /api/borsches/{borsch_id}/reviews/ - створити відгук (потрібна авторизація)
    - PATCH /api/reviews/{id}/ - оновити відгук (потрібна авторизація)
    - DELETE /api/reviews/{id}/ - видалити відгук (потрібна авторизація)
    
    Після створення/оновлення/видалення відгуку автоматично
    перераховуються агреговані рейтинги борщу.
    """
    queryset = Review.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnlyUA]
    pagination_class = CustomPageNumberPagination
    
    def get_serializer_class(self):
        """Вибір серіалізатора залежно від дії."""
        if self.action == 'create':
            return ReviewCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ReviewUpdateSerializer
        return ReviewSerializer
    
    def get_queryset(self):
        """
        Отримати список відгуків з фільтрацією по борщу.
        
        Параметр запиту:
        - borsch_id: фільтр по борщу (обов'язковий для list)
        """
        queryset = Review.objects.all().order_by('-created_at')
        
        # Фільтр по борщу
        borsch_id = self.request.query_params.get('borsch_id', None)
        if borsch_id:
            queryset = queryset.filter(borsch_id=borsch_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Створення відгуку з прив'язкою до користувача.
        
        Борщ передається в request body через поле `borsch`.
        Після створення перераховуються рейтинги відповідного борщу.
        """
        # Збереження відгуку
        review = serializer.save(
            user=self.request.user if self.request.user.is_authenticated else None
        )
        
        # Перерахунок рейтингів борщу
        self._recalculate_borsch_ratings(review.borsch)
    
    def perform_update(self, serializer):
        """
        Оновлення відгуку з перерахунком рейтингів борщу.
        """
        review = self.get_object()
        serializer.save()
        
        # Перерахунок рейтингів борщу
        self._recalculate_borsch_ratings(review.borsch)
    
    def perform_destroy(self, instance):
        """
        Видалення відгуку з перерахунком рейтингів борщу.
        """
        borsch = instance.borsch
        instance.delete()
        
        # Перерахунок рейтингів борщу
        self._recalculate_borsch_ratings(borsch)
    
    def _recalculate_borsch_ratings(self, borsch):
        """
        Перерахунок середніх оцінок для борщу.
        
        Обчислює середні значення всіх рейтингів по відгуках
        та оновлює поля моделі Borsch.
        """
        reviews = borsch.reviews.all()
        count = reviews.count()
        
        if count > 0:
            # Обчислення середніх значень
            borsch.rating_salt = sum(r.rating_salt for r in reviews) / count
            borsch.rating_meat = sum(r.rating_meat for r in reviews) / count
            borsch.rating_beet = sum(r.rating_beet for r in reviews) / count
            borsch.rating_density = sum(r.rating_density for r in reviews) / count
            borsch.rating_aftertaste = sum(r.rating_aftertaste for r in reviews) / count
            borsch.rating_serving = sum(r.rating_serving for r in reviews) / count
            borsch.overall_rating = sum(r.overall_rating for r in reviews) / count
        else:
            # Скидання оцінок якщо немає відгуків
            borsch.rating_salt = 0
            borsch.rating_meat = 0
            borsch.rating_beet = 0
            borsch.rating_density = 0
            borsch.rating_aftertaste = 0
            borsch.rating_serving = 0
            borsch.overall_rating = 0
        
        borsch.save()


# =============================================================================
# FavoriteBorsch ViewSet
# =============================================================================

class FavoriteBorschViewSet(viewsets.ModelViewSet):
    """
    ViewSet для обраних борщів.
    
    Підтримує CRUD операції:
    - GET /api/favorites/ - список обраних борщів користувача
    - POST /api/favorites/ - додати борщ до обраних (потрібна авторизація)
    - DELETE /api/favorites/{id}/ - видалити з обраних (потрібна авторизація)
    """
    queryset = FavoriteBorsch.objects.all()
    serializer_class = FavoriteBorschSerializer
    permission_classes = [IsAuthenticatedOrReadOnlyUA]
    pagination_class = CustomPageNumberPagination
    
    def get_queryset(self):
        """Отримати список обраних борщів поточного користувача."""
        if self.request.user.is_authenticated:
            return FavoriteBorsch.objects.filter(
                user=self.request.user
            ).order_by('-added_at')
        return FavoriteBorsch.objects.none()
    
    def perform_create(self, serializer):
        """Створення запису з прив'язкою до поточного користувача."""
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Потрібна авторизація для додавання до обраних')


# =============================================================================
# User ViewSet (для сумісності)
# =============================================================================

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для користувачів.
    
    Тільки читання (список та детальна інформація).
    Використовується для відображення авторів відгуків.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnlyUA]
    pagination_class = CustomPageNumberPagination
