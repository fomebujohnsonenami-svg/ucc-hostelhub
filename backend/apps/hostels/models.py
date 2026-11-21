from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from common.models import TimestampedModel, UUIDModel, VerificationStatus


class Amenity(UUIDModel):
    name = models.CharField(max_length=100, unique=True)
    icon_name = models.CharField(max_length=64, blank=True)

    class Meta:
        db_table = "amenities"


class Hostel(TimestampedModel):
    class PublicationStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending review"
        PUBLISHED = "published", "Published"
        HIDDEN = "hidden", "Hidden"

    manager = models.ForeignKey("accounts.ManagerProfile", on_delete=models.CASCADE, related_name="hostels")
    name = models.CharField(max_length=160)
    description = models.TextField()
    address = models.CharField(max_length=250)
    area = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, validators=[MinValueValidator(-90), MaxValueValidator(90)])
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, validators=[MinValueValidator(-180), MaxValueValidator(180)])
    verification_status = models.CharField(max_length=12, choices=VerificationStatus, default=VerificationStatus.PENDING)
    featured = models.BooleanField(default=False)
    publication_status = models.CharField(max_length=12, choices=PublicationStatus, default=PublicationStatus.DRAFT)
    amenities = models.ManyToManyField(Amenity, through="HostelAmenity", related_name="hostels", blank=True)

    class Meta:
        db_table = "hostels"
        indexes = [
            models.Index(fields=["publication_status", "area"], name="hostel_publication_area_idx"),
            models.Index(fields=["publication_status", "-updated_at"], name="hostel_publication_update_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(latitude__isnull=True, longitude__isnull=True) | Q(
                    latitude__isnull=False, longitude__isnull=False,
                    latitude__gte=-90, latitude__lte=90, longitude__gte=-180, longitude__lte=180,
                ), name="hostel_valid_coordinates",
            ),
        ]


class HostelAmenity(UUIDModel):
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE)
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE)

    class Meta:
        db_table = "hostel_amenities"
        constraints = [models.UniqueConstraint(fields=["hostel", "amenity"], name="unique_hostel_amenity")]


class HostelImage(UUIDModel):
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name="images")
    storage_path = models.CharField(max_length=300, unique=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "hostel_images"
        ordering = ["sort_order", "id"]
        indexes = [models.Index(fields=["hostel", "sort_order"], name="hostel_image_sort_idx")]


class RoomType(UUIDModel):
    class BillingPeriod(models.TextChoices):
        SEMESTER = "semester", "Semester"
        MONTH = "month", "Month"
        YEAR = "year", "Year"

    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name="room_types")
    name = models.CharField(max_length=100)
    capacity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    price_per_bed = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))], help_text="GHS")
    billing_period = models.CharField(max_length=12, choices=BillingPeriod, default=BillingPeriod.SEMESTER)
    total_rooms = models.PositiveSmallIntegerField(default=0)
    available_beds = models.PositiveIntegerField(default=0)
    amenities = models.JSONField(default=list, blank=True)
    availability_updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "room_types"
        indexes = [
            models.Index(fields=["billing_period", "price_per_bed"], name="room_period_price_idx"),
            models.Index(fields=["-availability_updated_at"], name="room_availability_update_idx"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(price_per_bed__gte=0), name="room_nonnegative_price"),
            models.CheckConstraint(condition=Q(capacity__gte=1), name="room_positive_capacity"),
            models.CheckConstraint(condition=Q(available_beds__gte=0, available_beds__lte=F("capacity") * F("total_rooms")), name="room_beds_within_capacity"),
        ]


class SavedHostel(UUIDModel):
    student = models.ForeignKey("accounts.Profile", on_delete=models.CASCADE, related_name="saved_hostels", limit_choices_to={"role": "student"})
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name="saves")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "saved_hostels"
        constraints = [models.UniqueConstraint(fields=["student", "hostel"], name="unique_student_saved_hostel")]
        indexes = [models.Index(fields=["student", "-created_at"], name="saved_student_recent_idx")]
