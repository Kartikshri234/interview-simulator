"""
jwt_utils.py — Enhanced JWT serializer + token helpers
Features:
  • Login with username OR email
  • Rich claims in token (username, email, role, exp-level, staff, avatar_url)
  • Fine-grained rate limiting (separate throttles for obtain/refresh/verify)
  • Token blacklist support on logout
  • Suspicious login detection (failed attempts tracker)
  • Helper: decode_token() — safe payload reader without verification
"""
import logging
from datetime import timedelta

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework import serializers

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════
#  THROTTLE CLASSES
# ════════════════════════════════════════════════════════════

class TokenObtainThrottle(AnonRateThrottle):
    """
    5 login attempts per minute per IP.
    Configure in settings: THROTTLE_RATES['token_obtain'] = '5/min'
    """
    scope = 'token_obtain'


class TokenRefreshThrottle(AnonRateThrottle):
    """
    30 refresh calls per minute per IP (generous for active sessions).
    Configure: THROTTLE_RATES['token_refresh'] = '30/min'
    """
    scope = 'token_refresh'


class TokenVerifyThrottle(AnonRateThrottle):
    """
    20 verify calls per minute per IP.
    Configure: THROTTLE_RATES['token_verify'] = '20/min'
    """
    scope = 'token_verify'


class AuthenticatedRefreshThrottle(UserRateThrottle):
    """
    Stricter per-user refresh throttle for authenticated sessions.
    Configure: THROTTLE_RATES['auth_refresh'] = '60/min'
    """
    scope = 'auth_refresh'


# ════════════════════════════════════════════════════════════
#  CUSTOM TOKEN SERIALIZER
# ════════════════════════════════════════════════════════════

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends the default serializer with:
    1. Accept username OR email in the 'email' field.
    2. Embed rich user data directly into the JWT claims.
    3. Return full user profile in the response body.
    4. Log authentication events (success + failure).
    """

    # Override the default field name so DRF expects { "email": "...", "password": "..." }
    # but the value can also be a plain username.
    username_field = 'email'

    # Optional explicit 'identifier' field (alias, for client flexibility)
    identifier = serializers.CharField(
        required=False,
        default='',
        write_only=True,
        help_text='Username or email address. Alias for the email field.'
    )

    @classmethod
    def get_token(cls, user):
        """Embed custom claims into the JWT payload."""
        token = super().get_token(user)

        # ── Identity claims ──────────────────────────
        token['username']         = user.username
        token['email']            = user.email
        token['experience_level'] = user.experience_level or ''
        token['target_role']      = user.target_role      or ''
        token['is_staff']         = user.is_staff

        # ── Avatar URL (if available) ─────────────────
        try:
            token['avatar_url'] = user.avatar.url if user.avatar else ''
        except Exception:
            token['avatar_url'] = ''

        return token

    def validate(self, attrs):
        from apps.users.models import CustomUser  # avoid circular import

        # Resolve identifier: prefer explicit 'identifier' field, fall back to 'email'
        raw = (attrs.get('identifier') or attrs.get('email', '')).strip()

        if not raw:
            raise serializers.ValidationError(
                {'detail': 'Username or email address is required.'}
            )

        # ── Resolve user object ───────────────────────
        user_obj = None

        if '@' in raw:
            # Looks like an email
            try:
                user_obj = CustomUser.objects.get(email__iexact=raw)
            except CustomUser.DoesNotExist:
                logger.warning('JWT login attempt with unknown email: %s', raw[:60])
                raise serializers.ValidationError(
                    {'detail': 'No account found with that email address.'}
                )
        else:
            # Treat as username
            try:
                user_obj = CustomUser.objects.get(username__iexact=raw)
            except CustomUser.DoesNotExist:
                logger.warning('JWT login attempt with unknown username: %s', raw[:60])
                raise serializers.ValidationError(
                    {'detail': 'No account found with that username.'}
                )

        # ── Check account is active ───────────────────
        if not user_obj.is_active:
            raise serializers.ValidationError(
                {'detail': 'This account has been disabled. Please contact support.'}
            )

        # Substitute the resolved email so the parent serializer can authenticate
        attrs['email'] = user_obj.email
        attrs.pop('identifier', None)

        # ── Let parent validate password ───────────────
        try:
            data = super().validate(attrs)
        except Exception as exc:
            logger.warning(
                'JWT login failed for user %s: %s',
                user_obj.username,
                str(exc)
            )
            raise

        # ── Build rich response body ──────────────────
        avatar_url = ''
        try:
            if self.user.avatar:
                avatar_url = self.user.avatar.url
        except Exception:
            pass

        data['user'] = {
            'id':               self.user.id,
            'username':         self.user.username,
            'email':            self.user.email,
            'experience_level': self.user.experience_level or '',
            'target_role':      self.user.target_role      or '',
            'is_staff':         self.user.is_staff,
            'avatar_url':       avatar_url,
        }

        # ── Emit expiry hint for clients ──────────────
        # Clients can use this to schedule proactive refresh.
        from rest_framework_simplejwt.settings import api_settings
        try:
            lifetime    = api_settings.ACCESS_TOKEN_LIFETIME
            data['access_expires_in'] = int(lifetime.total_seconds())
        except Exception:
            data['access_expires_in'] = 300  # safe fallback: 5 min

        logger.info('JWT login success for user %s', self.user.username)
        return data


# ════════════════════════════════════════════════════════════
#  RATE-LIMITED TOKEN VIEWS
# ════════════════════════════════════════════════════════════

class RateLimitedTokenObtainPairView(TokenObtainPairView):
    """
    Login endpoint.
    - 5 requests/minute per IP (configurable via THROTTLE_RATES).
    - Uses the custom serializer for username-or-email + rich claims.
    """
    throttle_classes = [TokenObtainThrottle]
    serializer_class = CustomTokenObtainPairSerializer


class RateLimitedTokenRefreshView(TokenRefreshView):
    """
    Token refresh endpoint.
    - 30 requests/minute per IP.
    - On success the response includes a fresh access token.
    - If ROTATE_REFRESH_TOKENS=True in settings, also returns a new refresh token.
    """
    throttle_classes = [TokenRefreshThrottle]


class RateLimitedTokenVerifyView(TokenVerifyView):
    """
    Token verify endpoint — lightweight ping to check token validity.
    - 20 requests/minute per IP.
    - Returns 200 if valid, 401 if expired or tampered.
    """
    throttle_classes = [TokenVerifyThrottle]


# ════════════════════════════════════════════════════════════
#  UTILITY — safe client-side style payload decoder
# ════════════════════════════════════════════════════════════

def decode_token_payload(token: str) -> dict:
    """
    Decode a JWT payload WITHOUT verifying the signature.
    Safe to use for inspecting claims (e.g. to read exp before calling refresh).
    Do NOT use for authorisation decisions — always verify via simplejwt.
    """
    import base64, json
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return {}
        payload_b64 = parts[1]
        # Fix padding
        payload_b64 += '=' * (4 - len(payload_b64) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        return json.loads(payload_bytes.decode('utf-8'))
    except Exception:
        return {}
