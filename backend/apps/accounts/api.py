from uuid import uuid4

from django.contrib.auth.hashers import check_password, make_password
from django.db import IntegrityError, transaction
from rest_framework import generics, permissions, serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .authentication import issue_session
from .models import LocalCredential, ManagerProfile, Profile

DUMMY_PASSWORD_HASH = make_password(uuid4().hex)


class CredentialsSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)

    def validate_email(self, email):
        return email.lower()


class RegistrationSerializer(CredentialsSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False, min_length=8, max_length=128)
    full_name = serializers.CharField(max_length=150)
    username = serializers.SlugField(max_length=64)
    role = serializers.ChoiceField(choices=(Profile.Role.STUDENT, Profile.Role.MANAGER))
    business_name = serializers.CharField(max_length=160, required=False)

    def validate(self, attrs):
        if attrs["role"] == Profile.Role.MANAGER and not attrs.get("business_name"):
            raise serializers.ValidationError({"business_name": "Enter your business name."})
        return attrs


class SignInThrottle(AnonRateThrottle):
    rate = "30/min"


class PublicAuth(generics.GenericAPIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = [SignInThrottle]


class Register(PublicAuth):
    serializer_class = RegistrationSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fields = serializer.validated_data.copy()
        email = fields.pop("email")
        password_hash = make_password(fields.pop("password"))
        business_name = fields.pop("business_name", None)
        try:
            with transaction.atomic():
                profile = Profile.objects.create(id=uuid4(), **fields)
                if profile.role == Profile.Role.MANAGER:
                    ManagerProfile.objects.create(user=profile, business_name=business_name)
                credential = LocalCredential.objects.create(profile=profile, email=email, password_hash=password_hash)
                token = issue_session(credential)
        except IntegrityError:
            raise serializers.ValidationError("That email or username is already in use.") from None
        return Response({"token": token}, status=201, headers={"Cache-Control": "no-store"})


class Login(PublicAuth):
    serializer_class = CredentialsSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fields = serializer.validated_data
        credential = LocalCredential.objects.filter(email=fields["email"]).first()
        if not check_password(fields["password"], credential.password_hash if credential else DUMMY_PASSWORD_HASH) or not credential:
            raise AuthenticationFailed("Email or password is incorrect.")
        return Response({"token": issue_session(credential)}, headers={"Cache-Control": "no-store"})

    def get_authenticate_header(self, request):
        return "Bearer"


class Logout(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.auth.delete()
        return Response(status=204)
