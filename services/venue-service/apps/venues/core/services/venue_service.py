"""
Venue Service Layer — Business logic for venue CRUD operations.

All write operations go through this layer. Views never touch models directly.
"""

import logging

from django.db import transaction
from django.utils.text import slugify

from apps.common.storage.base import get_storage_backend
from apps.venues.core.constants import ApprovalStatus
from apps.venues.core.exceptions import (
    CategoryNotFoundError,
    DuplicateVenueSlugError,
    ImageLimitExceededError,
    ImageNotFoundError,
    VenueNotFoundError,
    VenueOwnershipError,
)
from apps.venues.core.models import (
    Amenity,
    Venue,
    VenueAmenity,
    VenueCategory,
    VenueImage,
    VenuePolicy,
)

logger = logging.getLogger(__name__)


@transaction.atomic
def create_venue(*, vendor_id, tenant_id, data):
    """
    Create a new venue with amenities and policies.

    All venues start with approval_status=PENDING_APPROVAL.
    A platform admin must approve them before they appear publicly.
    """
    # 1. Validate category
    category_id = data.get("category_id")
    try:
        category = VenueCategory.objects.get(id=category_id, is_active=True)
    except VenueCategory.DoesNotExist as e:
        raise CategoryNotFoundError() from e

    # 2. Generate unique slug per tenant
    slug = slugify(data["name"])
    if Venue.objects.filter(tenant_id=tenant_id, slug=slug).exists():
        raise DuplicateVenueSlugError()

    # 3. Create venue
    venue = Venue.objects.create(
        vendor_id=vendor_id,
        tenant_id=tenant_id,
        category=category,
        name=data["name"],
        slug=slug,
        description=data.get("description", ""),
        address=data["address"],
        city=data["city"],
        state=data["state"],
        country=data.get("country", "India"),
        postal_code=data.get("postal_code", ""),
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
        capacity=data["capacity"],
        base_price=data["base_price"],
        price_type=data.get("price_type", "FULL_DAY"),
        approval_status=ApprovalStatus.PENDING_APPROVAL,
    )

    # 4. Attach amenities (bulk create join records)
    amenity_ids = data.get("amenity_ids", [])
    if amenity_ids:
        amenities = Amenity.objects.filter(id__in=amenity_ids, is_active=True)
        VenueAmenity.objects.bulk_create([VenueAmenity(venue=venue, amenity=amenity) for amenity in amenities])

    # 5. Create policies
    policies = data.get("policies", [])
    if policies:
        VenuePolicy.objects.bulk_create(
            [
                VenuePolicy(
                    venue=venue,
                    title=p["title"],
                    content=p["content"],
                    policy_type=p.get("policy_type", "GENERAL"),
                )
                for p in policies
            ]
        )

    logger.info(
        "Venue created: %s (tenant=%s, vendor=%s)",
        venue.id,
        tenant_id,
        vendor_id,
    )
    return venue


@transaction.atomic
def update_venue(*, venue_id, tenant_id, vendor_id, data):
    """Update a venue owned by the requesting vendor/tenant."""
    try:
        venue = Venue.objects.get(id=venue_id, tenant_id=tenant_id, is_active=True)
    except Venue.DoesNotExist as e:
        raise VenueNotFoundError() from e

    if venue.vendor_id != vendor_id:
        raise VenueOwnershipError()

    # Update simple fields
    updatable_fields = [
        "name",
        "description",
        "address",
        "city",
        "state",
        "country",
        "postal_code",
        "latitude",
        "longitude",
        "capacity",
        "base_price",
        "price_type",
    ]
    for field in updatable_fields:
        if field in data:
            setattr(venue, field, data[field])

    # Update category if provided
    if "category_id" in data:
        try:
            category = VenueCategory.objects.get(id=data["category_id"], is_active=True)
            venue.category = category
        except VenueCategory.DoesNotExist as e:
            raise CategoryNotFoundError() from e

    # Regenerate slug if name changed
    if "name" in data:
        new_slug = slugify(data["name"])
        if Venue.objects.filter(tenant_id=tenant_id, slug=new_slug).exclude(id=venue_id).exists():
            raise DuplicateVenueSlugError()
        venue.slug = new_slug

    venue.save()

    # Replace amenities if provided
    if "amenity_ids" in data:
        VenueAmenity.objects.filter(venue=venue).delete()
        amenities = Amenity.objects.filter(id__in=data["amenity_ids"], is_active=True)
        VenueAmenity.objects.bulk_create([VenueAmenity(venue=venue, amenity=amenity) for amenity in amenities])

    logger.info("Venue updated: %s", venue.id)
    return venue


def generate_image_upload_params(*, venue_id, tenant_id, vendor_id):
    """Generate signed upload params for client-side image uploads."""
    try:
        venue = Venue.objects.get(id=venue_id, tenant_id=tenant_id, is_active=True)
    except Venue.DoesNotExist as e:
        raise VenueNotFoundError() from e

    if venue.vendor_id != vendor_id:
        raise VenueOwnershipError()

    # Check image limit
    current_count = VenueImage.objects.filter(venue=venue).count()
    if current_count >= VenueImage.MAX_IMAGES_PER_VENUE:
        raise ImageLimitExceededError(f"Maximum {VenueImage.MAX_IMAGES_PER_VENUE} images per venue.")

    # Generate signed params via the storage abstraction
    backend = get_storage_backend()
    folder = f"venues/{venue_id}"
    params = backend.generate_signed_upload_params(folder=folder)

    return params


@transaction.atomic
def register_uploaded_image(*, venue_id, tenant_id, vendor_id, data):
    """
    Register an image that was uploaded directly to Cloudinary/S3 by the frontend.
    The frontend sends back the image_url and public_id after a successful upload.
    """
    try:
        venue = Venue.objects.get(id=venue_id, tenant_id=tenant_id, is_active=True)
    except Venue.DoesNotExist as e:
        raise VenueNotFoundError() from e

    if venue.vendor_id != vendor_id:
        raise VenueOwnershipError()

    current_count = VenueImage.objects.filter(venue=venue).count()
    if current_count >= VenueImage.MAX_IMAGES_PER_VENUE:
        raise ImageLimitExceededError(f"Maximum {VenueImage.MAX_IMAGES_PER_VENUE} images per venue.")

    is_primary = data.get("is_primary", False)

    # If this is set as primary, unset all other primary images
    if is_primary:
        VenueImage.objects.filter(venue=venue, is_primary=True).update(is_primary=False)

    # If this is the first image, auto-set as primary
    if current_count == 0:
        is_primary = True

    image = VenueImage.objects.create(
        venue=venue,
        image_url=data["image_url"],
        public_id=data.get("public_id", ""),
        caption=data.get("caption", ""),
        is_primary=is_primary,
        sort_order=data.get("sort_order", current_count),
    )

    logger.info("Image registered for venue %s: %s", venue_id, image.id)
    return image


def delete_venue_image(*, image_id, venue_id, tenant_id, vendor_id):
    """Delete a venue image from both the storage provider and the database."""
    try:
        venue = Venue.objects.get(id=venue_id, tenant_id=tenant_id, is_active=True)
    except Venue.DoesNotExist as e:
        raise VenueNotFoundError() from e

    if venue.vendor_id != vendor_id:
        raise VenueOwnershipError()

    try:
        image = VenueImage.objects.get(id=image_id, venue=venue)
    except VenueImage.DoesNotExist as e:
        raise ImageNotFoundError() from e

    # Delete from storage provider if public_id exists
    if image.public_id:
        backend = get_storage_backend()
        backend.delete_file(image.public_id)

    was_primary = image.is_primary
    image.delete()

    # If deleted image was primary, promote the next image
    if was_primary:
        next_image = VenueImage.objects.filter(venue=venue).first()
        if next_image:
            next_image.is_primary = True
            next_image.save(update_fields=["is_primary"])

    logger.info("Image %s deleted from venue %s", image_id, venue_id)
