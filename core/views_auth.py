"""HTTP-ендпоінти авторизації (Google OAuth + JWT)."""

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .oauth_google import (
    GoogleAccountConflictError,
    GoogleOAuthError,
    sync_user_from_google,
    verify_google_id_token,
)
from .serializers import UserProfileSerializer, UserSerializer
from .serializers_auth import GoogleIdTokenSerializer


class GoogleAuthView(APIView):
    """
    POST /api/auth/google/

    Тіло: {"id_token": "<JWT від Google>"}
    Відповідь: access, refresh, user, profile.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        ser = GoogleIdTokenSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        raw = ser.validated_data['id_token']

        try:
            info = verify_google_id_token(raw)
            user, profile, _created = sync_user_from_google(info)
        except GoogleOAuthError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except GoogleAccountConflictError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_409_CONFLICT)

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
                'profile': UserProfileSerializer(profile).data,
            },
            status=status.HTTP_200_OK,
        )
