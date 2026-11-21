import json
import re

from django.db import transaction
from django.db.models import Case, TextField, Value, When
from django.db.models.functions import Cast
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, serializers
from rest_framework.response import Response

from apps.accounts.models import Profile
from common.api import Page, StudentOnly

from .models import RoommateProfile

LIFESTYLES = ("Quiet", "Clean", "Studious", "Social", "Early riser", "Non-smoker")


class RoommateSerializer(serializers.ModelSerializer):
    lifestyle_preferences = serializers.ListField(child=serializers.ChoiceField(choices=LIFESTYLES), max_length=len(LIFESTYLES), required=False)
    moderation_hidden = serializers.BooleanField(read_only=True)
    compatibility = serializers.IntegerField(read_only=True, default=0)

    def validate(self, attrs):
        low = attrs.get("budget_min", getattr(self.instance, "budget_min", None))
        high = attrs.get("budget_max", getattr(self.instance, "budget_max", None))
        if low is not None and high is not None and low > high:
            raise serializers.ValidationError("Minimum budget must not exceed maximum budget.")
        for key in ("display_name", "description"):
            if re.search(r"@|(?:\d[\s().+\-]*){7,}", attrs.get(key, "")):
                raise serializers.ValidationError({key: "Remove personal email addresses and phone numbers."})
        if "lifestyle_preferences" in attrs:
            attrs["lifestyle_preferences"] = list(dict.fromkeys(attrs["lifestyle_preferences"]))
        return attrs

    class Meta:
        model = RoommateProfile
        fields = ("id", "display_name", "preferred_area", "budget_min", "budget_max", "student_level",
                  "lifestyle_preferences", "description", "visibility", "moderation_hidden", "compatibility")


class MatchFilters(serializers.Serializer):
    area = serializers.CharField(required=False, max_length=100)
    level = serializers.CharField(required=False, max_length=12)
    min = serializers.DecimalField(required=False, max_digits=12, decimal_places=2, min_value=0)
    max = serializers.DecimalField(required=False, max_digits=12, decimal_places=2, min_value=0)
    lifestyle = serializers.ListField(child=serializers.ChoiceField(choices=LIFESTYLES), required=False, max_length=len(LIFESTYLES))

    def validate(self, attrs):
        if "min" in attrs and "max" in attrs and attrs["min"] > attrs["max"]:
            raise serializers.ValidationError("Minimum budget must not exceed maximum budget.")
        return attrs


def visible_profiles():
    return RoommateProfile.objects.filter(visibility=RoommateProfile.Visibility.PUBLIC, moderation_hidden=False, student__role=Profile.Role.STUDENT)


class Roommates(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RoommateSerializer
    pagination_class = Page

    def get_queryset(self):
        data = self.request.query_params
        filters = MatchFilters(data={**data.dict(), "lifestyle": data.getlist("lifestyle")})
        filters.is_valid(raise_exception=True)
        options = filters.validated_data
        queryset = visible_profiles().alias(lifestyle_text=Cast("lifestyle_preferences", TextField()))
        user = self.request.user
        own = None
        if user.is_authenticated:
            queryset = queryset.exclude(student=user)
            own = RoommateProfile.objects.filter(student=user).first()
        score = Value(0)
        if area := options.get("area"):
            queryset = queryset.filter(preferred_area__iexact=area)
        if level := options.get("level"):
            queryset = queryset.filter(student_level=level)
        if "min" in options:
            queryset = queryset.filter(budget_max__gte=options["min"])
        if "max" in options:
            queryset = queryset.filter(budget_min__lte=options["max"])
        for preference in set(options["lifestyle"]):
            queryset = queryset.filter(lifestyle_text__icontains=json.dumps(preference))
        if own:
            score += Case(When(budget_min__lte=own.budget_max, budget_max__gte=own.budget_min, then=Value(3)), default=Value(0))
            score += Case(When(preferred_area__iexact=own.preferred_area, then=Value(2)), default=Value(0))
            for preference in set(own.lifestyle_preferences).intersection(LIFESTYLES):
                score += Case(When(lifestyle_text__icontains=json.dumps(preference), then=Value(1)), default=Value(0))
        return queryset.annotate(compatibility=score).order_by("-compatibility", "-updated_at", "pk")


class RoommateDetail(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RoommateSerializer
    queryset = visible_profiles()


class OwnRoommate(generics.GenericAPIView):
    permission_classes = [StudentOnly]
    serializer_class = RoommateSerializer

    def get(self, request):
        return Response(self.get_serializer(get_object_or_404(RoommateProfile, student=request.user)).data)

    @transaction.atomic
    def put(self, request):
        Profile.objects.select_for_update().get(pk=request.user.pk)
        instance = RoommateProfile.objects.filter(student=request.user).first()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(student=request.user)
        return Response(serializer.data, status=200 if instance else 201)
