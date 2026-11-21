from django.conf import settings
from django.db.models import Min, OuterRef, Subquery
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import RoomType


class DiscoveryFilters(serializers.Serializer):
    q = serializers.CharField(required=False, max_length=160)
    area = serializers.CharField(required=False, max_length=100)
    room = serializers.CharField(required=False, max_length=100)
    min = serializers.DecimalField(required=False, max_digits=12, decimal_places=2, min_value=0)
    max = serializers.DecimalField(required=False, max_digits=12, decimal_places=2, min_value=0)
    available = serializers.ChoiceField(required=False, choices=("yes", "no"))
    sort = serializers.ChoiceField(required=False, choices=("latest", "low", "high"))
    amenity = serializers.ListField(child=serializers.CharField(max_length=100), required=False, max_length=20)

    def validate(self, attrs):
        if "min" in attrs and "max" in attrs and attrs["min"] > attrs["max"]:
            raise ValidationError("Minimum price must not exceed maximum price.")
        return attrs


def filter_hostels(queryset, params):
    from django.db.models import Exists, F, Q

    filters = DiscoveryFilters(data={**params.dict(), "amenity": params.getlist("amenity")})
    filters.is_valid(raise_exception=True)
    options = filters.validated_data
    if term := options.get("q"):
        queryset = queryset.filter(Q(name__icontains=term) | Q(area__icontains=term) | Q(address__icontains=term))
    if area := options.get("area"):
        queryset = queryset.filter(area__iexact=area)
    for amenity in set(options["amenity"]):
        queryset = queryset.filter(amenities__name__iexact=amenity)
    rooms = RoomType.objects.filter(hostel=OuterRef("pk"))
    if "room" in options:
        rooms = rooms.filter(name__iexact=options["room"])
    if options.get("available") == "yes":
        rooms = rooms.filter(available_beds__gt=0)
    if "min" in options or "max" in options:
        rooms = rooms.filter(billing_period=RoomType.BillingPeriod.SEMESTER)
        if "min" in options:
            rooms = rooms.filter(price_per_bed__gte=options["min"])
        if "max" in options:
            rooms = rooms.filter(price_per_bed__lte=options["max"])
    if any(key in options for key in ("min", "max", "room")) or options.get("available") == "yes":
        queryset = queryset.filter(Exists(rooms))
    sort = options.get("sort")
    if sort in {"low", "high"}:
        semester = rooms.filter(billing_period=RoomType.BillingPeriod.SEMESTER).order_by()
        price = semester.values("hostel").annotate(lowest=Min("price_per_bed")).values("lowest")
        queryset = queryset.annotate(semester_price=Subquery(price))
        order = F("semester_price").asc(nulls_last=True) if sort == "low" else F("semester_price").desc(nulls_last=True)
        return queryset.order_by(order, "pk")
    return queryset.order_by("-updated_at", "pk")


def availability_stale(room):
    return (timezone.now() - room.availability_updated_at).total_seconds() >= settings.AVAILABILITY_STALE_HOURS * 3600
