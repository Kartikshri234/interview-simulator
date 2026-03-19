from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser


# ── Serializers ───────────────────────────────────────────────
class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model  = CustomUser
        fields = ('username', 'email', 'password', 'password2', 'target_role', 'experience_level')

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CustomUser
        fields = ('id', 'username', 'email', 'bio', 'avatar',
                  'target_role', 'experience_level', 'created_at')
        read_only_fields = ('id', 'email', 'created_at')


# ── API Views ─────────────────────────────────────────────────
class RegisterAPIView(generics.CreateAPIView):
    queryset         = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class   = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


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
