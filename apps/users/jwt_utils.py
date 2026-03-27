"""
jwt_utils.py — Custom JWT serializer + token helpers
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
    Fixes the username_field so simplejwt uses 'email' as the login
    credential (matching CustomUser.USERNAME_FIELD = 'email').

    Without this override, the default serializer still labels its
    credential field 'username' which means the frontend must send
    { username: '...' } instead of { email: '...' } — causing 400s.
    """

    # ← THIS is the critical fix: tell simplejwt the login field is 'email'
    username_field = 'email'

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Identity claims embedded in the access token
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
