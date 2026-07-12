from django.contrib import admin

from apps.venues.core.models import (
    Amenity,
    Venue,
    VenueAmenity,
    VenueCategory,
    VenueImage,
    VenuePolicy,
)


class VenueImageInline(admin.TabularInline):
    model = VenueImage
    extra = 0
    readonly_fields = ("id", "created_at")


class VenueAmenityInline(admin.TabularInline):
    model = VenueAmenity
    extra = 0


class VenuePolicyInline(admin.TabularInline):
    model = VenuePolicy
    extra = 0


@admin.register(VenueCategory)
class VenueCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "created_at")
    search_fields = ("name",)
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "capacity", "base_price", "approval_status", "is_active")
    list_filter = ("approval_status", "is_active", "price_type", "city")
    search_fields = ("name", "city")
    readonly_fields = ("id", "vendor_id", "tenant_id", "created_at", "updated_at")
    inlines = [VenueImageInline, VenueAmenityInline, VenuePolicyInline]
