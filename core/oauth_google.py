"""
Верифікація Google ID token та синхронізація User / UserProfile.

Клієнт (Web / мобільний застосунок) отримує `id_token` від Google і надсилає його
на `POST /api/auth/google/`. Бекенд перевіряє підпис і `aud` (Client ID),
потім створює або оновлює записи в БД.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from .models import UserProfile


class GoogleOAuthError(Exception):
    """Невалідний токен, конфігурація сервера або дані в токені."""


class GoogleAccountConflictError(Exception):
    """Неможливо безпечно прив'язати Google-акаунт до локального користувача."""


@dataclass(frozen=True)
class GoogleUserInfo:
    sub: str
    email: str
    given_name: str
    surname: str
    locale: str
    picture: str

    @classmethod
    def from_claims(cls, claims: dict[str, Any]) -> GoogleUserInfo:
        email = (claims.get('email') or '').strip().lower()
        if not email:
            raise GoogleOAuthError('У токені Google відсутній email')
        if claims.get('email_verified') is not True:
            raise GoogleOAuthError('Email у Google не підтверджено (email_verified)')

        given = (claims.get('given_name') or '').strip()
        if not given:
            name = (claims.get('name') or '').strip()
            given = (name.split(' ', 1)[0] if name else '') or email.split('@', 1)[0]
        given = given[:100]

        surname = ((claims.get('family_name') or '').strip())[:100]
        locale = ((claims.get('locale') or '').strip())[:20]
        picture = ((claims.get('picture') or '').strip())[:200]

        return cls(
            sub=str(claims['sub']),
            email=email,
            given_name=given,
            surname=surname,
            locale=locale,
            picture=picture,
        )


def verify_google_id_token(token: str) -> GoogleUserInfo:
    audiences = getattr(settings, 'GOOGLE_OAUTH_CLIENT_IDS', []) or []
    if not audiences:
        raise GoogleOAuthError(
            'Не задано GOOGLE_OAUTH_CLIENT_IDS (або GOOGLE_OAUTH_CLIENT_ID) у середовищі'
        )

    aud: str | list[str]
    aud = audiences[0] if len(audiences) == 1 else audiences

    try:
        claims = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            audience=aud,
        )
    except ValueError as exc:
        raise GoogleOAuthError('Невірний або прострочений Google ID token') from exc

    iss = claims.get('iss')
    if iss not in ('accounts.google.com', 'https://accounts.google.com'):
        raise GoogleOAuthError('Невірний issuer (iss) у Google ID token')

    return GoogleUserInfo.from_claims(claims)


def _unique_username(email: str) -> str:
    local = (email.split('@', 1)[0] or 'user').strip() or 'user'
    base = ''.join(c if c.isalnum() else '_' for c in local)[:40] or 'user'
    candidate = base
    n = 0
    while User.objects.filter(username=candidate).exists():
        n += 1
        suffix = f'_{n}'
        candidate = (base[: 150 - len(suffix)] + suffix)
    return candidate[:150]


def _apply_profile_fields(profile: UserProfile, info: GoogleUserInfo) -> None:
    profile.google_id = info.sub
    profile.given_name = info.given_name
    profile.surname = info.surname
    profile.locale = info.locale
    if info.picture:
        profile.avatar_url = info.picture


@transaction.atomic
def sync_user_from_google(info: GoogleUserInfo) -> tuple[User, UserProfile, bool]:
    """
    Повертає (user, profile, created_profile).

    created_profile=True лише коли щойно створено UserProfile для нового користувача
    або для існуючого User без профілю.
    """
    profile = (
        UserProfile.objects.select_related('user')
        .filter(google_id=info.sub)
        .first()
    )
    if profile:
        _apply_profile_fields(profile, info)
        profile.save()
        user = profile.user
        if user.email.lower() != info.email:
            user.email = info.email
            user.save(update_fields=['email'])
        return user, profile, False

    users = list(User.objects.filter(email__iexact=info.email).order_by('id'))
    if len(users) > 1:
        raise GoogleAccountConflictError(
            'Знайдено кілька облікових записів з однаковим email; зверніться до підтримки'
        )

    if users:
        user = users[0]
        try:
            existing_profile = user.profile
        except UserProfile.DoesNotExist:
            profile = UserProfile(
                user=user,
                given_name=info.given_name,
            )
            _apply_profile_fields(profile, info)
            profile.save()
            if user.email.lower() != info.email:
                user.email = info.email
                user.save(update_fields=['email'])
            return user, profile, True

        if existing_profile.google_id and existing_profile.google_id != info.sub:
            raise GoogleAccountConflictError(
                'Цей email уже прив\'язаний до іншого Google-акаунта'
            )
        _apply_profile_fields(existing_profile, info)
        existing_profile.save()
        if user.email.lower() != info.email:
            user.email = info.email
            user.save(update_fields=['email'])
        return user, existing_profile, False

    username = _unique_username(info.email)
    user = User(username=username, email=info.email)
    user.set_unusable_password()
    user.save()

    profile = UserProfile(
        user=user,
        given_name=info.given_name,
    )
    _apply_profile_fields(profile, info)
    profile.save()
    return user, profile, True
