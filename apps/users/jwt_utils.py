"""
jwt_utils.py — Custom JWT serializer + token helpers
Supports login with EITHER username OR email address.
"""
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.throttling import AnonRateThrottle
from rest_framework import serializers


# ── Custom throttle classes ──────────────────────────────────

class TokenObtainThrottle(AnonRateThrottle):
    """5 login attempts per minute per IP."""
    scope = 'token_obtain'


class TokenRefreshThrottle(AnonRateThrottle):
    """10 refresh calls per minute per IP."""
    scope = 'token_refresh'


# ── Custom token serializer with username-or-email support ────

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Allows the user to log in using either their username OR email.
    The frontend sends { email: "...", password: "..." } where 'email'
    can be either an actual email address or a username.
    """
    username_field = 'email'

    # Optional explicit identifier field
    identifier = serializers.CharField(required=False, default='', write_only=True)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username']         = user.username
        token['email']            = user.email
        token['experience_level'] = user.experience_level
        token['target_role']      = user.target_role or ''
        token['is_staff']         = user.is_staff
        return token

    def validate(self, attrs):
        from apps.users.models import CustomUser

        raw = (attrs.get('identifier') or attrs.get('email', '')).strip()

        if not raw:
            raise serializers.ValidationError('Username or email is required.')

        if '@' in raw:
            try:
                user_obj = CustomUser.objects.get(email__iexact=raw)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError(
                    {'detail': 'No account found with that email address.'}
                )
        else:
            try:
                user_obj = CustomUser.objects.get(username__iexact=raw)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError(
                    {'detail': 'No account found with that username.'}
                )

        attrs['email'] = user_obj.email
        attrs.pop('identifier', None)

        data = super().validate(attrs)

        # Attach user profile to the response
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
