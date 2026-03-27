"""
api_views.py — REST API views for the users app
"""
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import check_password
from django.contrib.auth import authenticate
from .models import CustomUser


# ── Throttle classes ──────────────────────────────────────────

class RegisterThrottle(AnonRateThrottle):
    scope = 'token_obtain'


# ── Username-or-email JWT serializer ─────────────────────────

class FlexTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Overrides the default JWT login to accept either a username OR
    an email address in the 'email' field (or a new 'identifier' field).
    """
    # Add an 'identifier' field; keep 'email' as well for backwards compat
    identifier = serializers.CharField(required=False, default='')

    def validate(self, attrs):
        # Support both 'identifier' (new) and 'email' (legacy) field names
        identifier = (attrs.get('identifier') or attrs.get('email', '')).strip()
        password   = attrs.get('password', '')

        if not identifier or not password:
            raise serializers.ValidationError('Identifier and password are required.')

        # Resolve identifier → email (our USERNAME_FIELD)
        if '@' in identifier:
            try:
                user_obj = CustomUser.objects.get(email__iexact=identifier)
                resolved_email = user_obj.email
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError('No account found with that email.')
        else:
            try:
                user_obj = CustomUser.objects.get(username__iexact=identifier)
                resolved_email = user_obj.email
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError('No account found with that username.')

        # Now authenticate with the resolved email
        attrs[self.username_field] = resolved_email
        return super().validate(attrs)


class FlexTokenObtainPairView(TokenObtainPairView):
    serializer_class = FlexTokenObtainPairSerializer


# ── Serializers ───────────────────────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model  = CustomUser
        fields = ('username', 'email', 'password', 'password2',
                  'target_role', 'experience_level')

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        if CustomUser.objects.filter(email__iexact=attrs['email']).exists():
            raise serializers.ValidationError({'email': 'An account with that email already exists.'})
        if CustomUser.objects.filter(username__iexact=attrs['username']).exists():
            raise serializers.ValidationError({'username': 'That username is already taken.'})
        return attrs

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CustomUser
        fields = ('id', 'username', 'email', 'bio', 'avatar',
                  'target_role', 'experience_level', 'created_at')
        read_only_fields = ('id', 'email', 'created_at')


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, required=True)
    new_password     = serializers.CharField(write_only=True, required=True,
                                             validators=[validate_password])
    new_password2    = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password': 'New passwords do not match.'})
        return attrs


# ── API Views ─────────────────────────────────────────────────

class RegisterAPIView(generics.CreateAPIView):
    queryset           = CustomUser.objects.all()
    serializer_class   = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes   = [RegisterThrottle]


class ProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class   = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'Refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)


class ChangePasswordAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not check_password(serializer.validated_data['current_password'], user.password):
            return Response({'detail': 'Current password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)
        if check_password(serializer.validated_data['new_password'], user.password):
            return Response({'detail': 'New password must be different from the current password.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        return Response({'detail': 'Password changed successfully. Please log in again.'}, status=status.HTTP_200_OK)


class UserStatsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from apps.interview.models import InterviewSession
        from django.db.models import Avg, Count, Q
        data = InterviewSession.objects.filter(user=request.user).aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(status='completed')),
            avg_score=Avg('overall_score'),
        )
        return Response({
            'total_sessions':     data['total'] or 0,
            'completed_sessions': data['completed'] or 0,
            'average_score':      round(data['avg_score'] or 0, 1),
        })
