"""Серіалізатори для ендпоінтів авторизації."""

from rest_framework import serializers


class GoogleIdTokenSerializer(serializers.Serializer):
    id_token = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        help_text='Google ID token (JWT) з Google Sign-In',
    )
