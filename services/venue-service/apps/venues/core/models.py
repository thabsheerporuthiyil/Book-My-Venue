import uuid

from bmv_libraries.common.outbox.models import AbstractOutboxModel
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from .constants import ApprovalStatus, PolicyType, PolicyValue, PriceType, VenueStaffRole


class SoftDeleteMixin(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    @property
    def is_deleted(self):
        return self.deleted_at is not None


# =============================================================================
# 1. VenueCategory
# =============================================================================


class VenueCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="subcategories")
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    icon = models.CharField(max_length=100, blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "venues_category"
        verbose_name_plural = "Venue Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# =============================================================================
# 2. Amenity
# =============================================================================


class Amenity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    icon = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "venues_amenity"
        verbose_name_plural = "Amenities"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# =============================================================================
# VenueTag (New)
# =============================================================================


class VenueTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "venues_tag"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


# =============================================================================
# 3. Venue (Core Entity)
# =============================================================================


class Venue(SoftDeleteMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    vendor_id = models.UUIDField(db_index=True, help_text="References User in auth-service")
    tenant_id = models.UUIDField(db_index=True, help_text="References Tenant in auth-service")

    category = models.ForeignKey(VenueCategory, on_delete=models.PROTECT, related_name="venues")

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, db_index=True)
    description = models.TextField(blank=True, default="")

    # Contact Info
    contact_phone = models.CharField(max_length=20, blank=True, default="")
    contact_email = models.EmailField(blank=True, default="")
    website_url = models.URLField(blank=True, default="")

    # Address & Geolocation
    address = models.CharField(max_length=500)
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="India")
    postal_code = models.CharField(max_length=20, blank=True, default="")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Core Business fields
    capacity = models.PositiveIntegerField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    price_type = models.CharField(max_length=20, choices=PriceType.choices, default=PriceType.FULL_DAY)

    # Cached Ratings
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    review_count = models.PositiveIntegerField(default=0)

    # Search & AI Metadata
    search_text = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    ai_embedding_hash = models.CharField(max_length=64, blank=True, default="")

    approval_status = models.CharField(
        max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING_APPROVAL, db_index=True
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "venues_venue"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["tenant_id", "slug"], name="unique_venue_slug_per_tenant"),
        ]
        indexes = [
            models.Index(fields=["city", "approval_status"], name="idx_city_approval"),
            models.Index(fields=["category", "approval_status"], name="idx_category_approval"),
            models.Index(fields=["city", "category"], name="idx_city_category"),
            models.Index(fields=["latitude", "longitude"], name="idx_venue_geolocation"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.search_text = f"{self.name} {self.description} {self.city} {self.state}".strip().lower()
        super().save(*args, **kwargs)


# =============================================================================
# VenueStaff (New)
# =============================================================================


class VenueStaff(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="staff_members")
    user_id = models.UUIDField(help_text="References User in auth-service")
    role = models.CharField(max_length=20, choices=VenueStaffRole.choices, default=VenueStaffRole.VENUE_STAFF)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "venues_venuestaff"
        unique_together = ("venue", "user_id")

    def __str__(self):
        return f"{self.user_id} - {self.venue.name} ({self.role})"


# =============================================================================
# VenueOwnershipTransfer (New)
# =============================================================================


class VenueOwnershipTransfer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="ownership_transfers")
    from_vendor_id = models.UUIDField()
    to_vendor_id = models.UUIDField()
    from_tenant_id = models.UUIDField()
    to_tenant_id = models.UUIDField()
    transferred_by = models.UUIDField(help_text="User who initiated the transfer")
    reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "venues_ownership_transfer"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Transfer of {self.venue.name}"


# =============================================================================
# 4. VenueImage
# =============================================================================


class VenueImage(SoftDeleteMixin):
    MAX_IMAGES_PER_VENUE = 10

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="images")
    image_url = models.URLField(max_length=500)
    public_id = models.CharField(max_length=255, blank=True, default="")
    caption = models.CharField(max_length=255, blank=True, default="")
    alt_text = models.CharField(max_length=255, blank=True, default="")
    is_primary = models.BooleanField(default=False, db_index=True)
    sort_order = models.PositiveIntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "venues_venueimage"
        ordering = ["sort_order", "created_at"]

    def __str__(self):
        return f"Image for {self.venue.name} (primary={self.is_primary})"


# =============================================================================
# 5. VenueAmenity (Join Table)
# =============================================================================


class VenueAmenity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="venue_amenities")
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE, related_name="venue_amenities")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "venues_venueamenity"
        constraints = [
            models.UniqueConstraint(fields=["venue", "amenity"], name="unique_venue_amenity"),
        ]

    def __str__(self):
        return f"{self.amenity.name} at {self.venue.name}"


# =============================================================================
# VenueTagAssignment (New Join Table)
# =============================================================================


class VenueTagAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="venue_tags")
    tag = models.ForeignKey(VenueTag, on_delete=models.CASCADE, related_name="venue_tags")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "venues_venuetagassignment"
        constraints = [
            models.UniqueConstraint(fields=["venue", "tag"], name="unique_venue_tag"),
        ]

    def __str__(self):
        return f"{self.tag.name} on {self.venue.name}"


# =============================================================================
# 6. VenuePolicy
# =============================================================================


class VenuePolicy(SoftDeleteMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="policies")
    policy_type = models.CharField(max_length=20, choices=PolicyType.choices, db_index=True)
    policy_value = models.CharField(max_length=20, choices=PolicyValue.choices, default=PolicyValue.CUSTOM)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "venues_venuepolicy"
        verbose_name_plural = "Venue Policies"
        ordering = ["policy_type", "created_at"]
        unique_together = ("venue", "policy_type")

    def __str__(self):
        return f"{self.policy_type} for {self.venue.name}"


# =============================================================================
# VenuePricingTier (New)
# =============================================================================


class VenuePricingTier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="pricing_tiers")
    label = models.CharField(max_length=100)
    price_type = models.CharField(max_length=20, choices=PriceType.choices)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "venues_pricing_tier"
        ordering = ["sort_order", "created_at"]

    def __str__(self):
        return f"{self.label} tier for {self.venue.name}"


# =============================================================================
# VenueApprovalLog (New)
# =============================================================================


class VenueApprovalLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="approval_logs")
    old_status = models.CharField(max_length=20, choices=ApprovalStatus.choices, blank=True, default="")
    new_status = models.CharField(max_length=20, choices=ApprovalStatus.choices)
    changed_by = models.UUIDField(help_text="User who made the change")
    reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "venues_approval_log"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Status {self.new_status} for {self.venue.name}"


# =============================================================================
# VenueReview (New)
# =============================================================================


class VenueReview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="reviews")
    reviewer_id = models.UUIDField(help_text="References User in auth-service")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_verified = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    helpful_count = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "venues_review"
        unique_together = ("venue", "reviewer_id")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.rating} star review for {self.venue.name}"


# =============================================================================
# VenueOperatingHour (New)
# =============================================================================


class VenueOperatingHour(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name="operating_hours")
    day_of_week = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(6)])
    open_time = models.TimeField()
    close_time = models.TimeField()
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "venues_operating_hour"
        unique_together = ("venue", "day_of_week")
        ordering = ["day_of_week"]

    def __str__(self):
        return f"Day {self.day_of_week} hours for {self.venue.name}"


# =============================================================================
# OutboxEvent (Transactional Outbox)
# =============================================================================


class OutboxEvent(AbstractOutboxModel):
    """
    Concrete implementation of the Outbox pattern for the Venue Service.
    Saves events in the same database transaction as business entities.
    """

    class Meta(AbstractOutboxModel.Meta):
        db_table = "venues_outbox_event"
