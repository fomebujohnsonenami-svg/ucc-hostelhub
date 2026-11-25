from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, serializers
from rest_framework.response import Response

from apps.hostels.models import Hostel
from common.api import ManagerOnly, Page
from common.models import VerificationStatus

from .access import access_mode
from .models import SubscriptionPlan


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ("audience", "name", "price", "billing_period", "features")


class Plans(generics.GenericAPIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True, audience__in=SubscriptionPlan.Audience.values).order_by("-audience")
        return Response({"access_mode": access_mode(), "payments_available": False, "plans": PlanSerializer(plans, many=True).data})


def eligible_for_promotion(hostel):
    return hostel.publication_status == Hostel.PublicationStatus.PUBLISHED and hostel.verification_status != VerificationStatus.REJECTED


class PromotionSerializer(serializers.ModelSerializer):
    inquiries = serializers.IntegerField(read_only=True)
    eligible = serializers.SerializerMethodField()

    def get_eligible(self, hostel):
        return eligible_for_promotion(hostel)

    class Meta:
        model = Hostel
        fields = ("id", "name", "area", "featured", "eligible", "inquiries")


class Promotions(generics.ListAPIView):
    permission_classes = [ManagerOnly]
    serializer_class = PromotionSerializer
    pagination_class = Page

    def get_queryset(self):
        return Hostel.objects.filter(manager__user=self.request.user).annotate(
            inquiries=Count("conversations"),
        ).order_by("-featured", "name", "pk")


class PromotionInput(serializers.Serializer):
    featured = serializers.BooleanField()


class Promotion(generics.GenericAPIView):
    permission_classes = [ManagerOnly]
    serializer_class = PromotionInput

    @transaction.atomic
    def patch(self, request, pk):
        hostel = get_object_or_404(Hostel.objects.filter(manager__user=request.user).select_for_update(of=("self",)), pk=pk)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        featured = serializer.validated_data["featured"]
        if featured and not eligible_for_promotion(hostel):
            raise serializers.ValidationError({"featured": "Only published listings can be featured."})
        hostel.featured = featured
        hostel.save(update_fields=["featured"])
        return Response({"featured": hostel.featured})
