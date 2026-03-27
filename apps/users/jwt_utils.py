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

    The frontend can send:
      { "email": "user@example.com", "password": "..." }   ← email login
      { "email": "johndoe",          "password": "..." }   ← username login
      { "identifier": "...",         "password": "..." }   ← either (new field)

    We resolve the identifier to the account's email before passing
    it to simplejwt (which uses email as the USERNAME_FIELD).
    """

    # Keep 'email' as the primary field name for backwards-compat with
    # the existing frontend (common.js sends { email, password }).
    # We also accept an optional 'identifier' field.
    username_field = 'email'

    # Add an optional 'identifier' field so callers can be explicit
    identifier = serializers.CharField(required=False, default='', write_only=True)

    def validate(self, attrs):
        from apps.users.models import CustomUser

        # Accept 'identifier' OR 'email' field as the login credential
        raw = (attrs.get('identifier') or attrs.get('email', '')).strip()

        if not raw:
            raise serializers.ValidationError('Username or email is required.')

        # Resolve to the account's canonical email address
        if '@' in raw:
            # Treat as email
            try:
                user_obj = CustomUser.objects.get(email__iexact=raw)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError(
                    {'email': 'No account found with that email address.'}
                )
        else:
            # Treat as username
            try:
                user_obj = CustomUser.objects.get(username__iexact=raw)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError(
                    {'email': 'No account found with that username.'}
                )

        # Inject the resolved email so the parent serializer can authenticate
        attrs['email'] = user_obj.email

        # Remove the extra field before calling super() — it doesn't expect it
        attrs.pop('identifier', None)

        return super().validate(attrs)

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

        # Call grandparent validate to get the token pair
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
