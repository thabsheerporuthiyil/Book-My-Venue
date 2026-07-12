from django.db import models


class OutboxStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    PUBLISHED = "PUBLISHED", "Published"
    FAILED = "FAILED", "Failed"
    DEAD = "DEAD", "Dead Letter"


class AbstractOutboxModel(models.Model):
    """
    Abstract outbox model for reliable event publishing.
    Every service should inherit this to create its own local outbox table.
    """

    event_id = models.UUIDField(unique=True)
    event_type = models.CharField(max_length=100)
    event_version = models.PositiveSmallIntegerField(default=1)
    topic = models.CharField(max_length=255)
    partition_key = models.CharField(max_length=255)
    payload = models.JSONField()
    headers = models.JSONField(default=dict)

    status = models.CharField(max_length=20, choices=OutboxStatus.choices, default=OutboxStatus.PENDING, db_index=True)

    retry_count = models.PositiveSmallIntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)

    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["status", "next_attempt_at"], name="idx_outbox_processing"),
        ]
