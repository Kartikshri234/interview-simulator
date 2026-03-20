"""
jwt_utils.py — Custom JWT serializer + token helpers

Embeds extra user claims into the access token payload so the
frontend can read username, email, role and level without an
extra /profile/ round-trip.
"""
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.throttling import AnonRateThrottle


# ── Custom throttle classes ──────────────────────────────────

class TokenObtainThrottle(AnonRateThrottle):
    """5 login attempts per minute per IP."""
    scope = 'token_obtain'


class TokenRefreshThrottle(AnonRateThrottle):
    """10 refresh calls per minute per IP."""
    scope = 'token_refresh'


# ── Custom token serializer with extra claims ─────────────────

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Adds the following claims to the ACCESS token payload:
      - username
      - email
      - experience_level
      - target_role
      - is_staff
    These are readable by the frontend (e.g. to show the user's name
    in the navbar) without decoding needing a separate API call.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Identity claims
        token['username']         = user.username
        token['email']            = user.email

        # Profile claims
        token['experience_level'] = user.experience_level
        token['target_role']      = user.target_role or ''

        # Permission hint (never trust this alone — always verify server-side)
        token['is_staff']         = user.is_staff

        return token

    def validate(self, attrs):
        """
        Extends the default response to include user profile data
        alongside the tokens so the client can bootstrap state immediately.
        """
        data = super().validate(attrs)

        data['user'] = {
            'id':               self.user.id,
            'username':         self.user.username,
            'email':            self.user.email,
            'experience_level': self.user.experience_level,
            'target_role':      self.user.target_role or '',
            'is_staff':         self.user.is_staff,
        }

        return data


# ── Rate-limited token views ──────────────────────────────────

class RateLimitedTokenObtainPairView(TokenObtainPairView):
    """Login endpoint — max 5 requests/minute per IP."""
    throttle_classes = [TokenObtainThrottle]
    serializer_class = CustomTokenObtainPairSerializer


class RateLimitedTokenRefreshView(TokenRefreshView):
    """Refresh endpoint — max 10 requests/minute per IP."""
    throttle_classes = [TokenRefreshThrottle]
