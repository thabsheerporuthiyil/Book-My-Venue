"""
Cloudinary Storage Backend.

Generates signed upload parameters so the frontend (React) can upload
images directly to Cloudinary without routing them through Django.

Why client-side uploads?
  - Django never touches the raw file bytes → zero memory/CPU overhead.
  - Cloudinary handles resizing, compression, and CDN distribution.
  - The signed params ensure only authorized uploads occur.
"""

import logging
import time

import cloudinary
import cloudinary.api
import cloudinary.uploader
import cloudinary.utils
from django.conf import settings

from .base import BaseStorageBackend

logger = logging.getLogger(__name__)


class CloudinaryStorageBackend(BaseStorageBackend):
    """Concrete storage backend for Cloudinary."""

    def __init__(self):
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True,
        )

    def generate_signed_upload_params(self, folder: str, **kwargs) -> dict:
        """
        Generate signed parameters for a direct browser-to-Cloudinary upload.

        The frontend uses these params with Cloudinary's Upload Widget or
        a simple fetch() POST to https://api.cloudinary.com/v1_1/{cloud}/image/upload.

        Args:
            folder: The Cloudinary folder path (e.g., "venues/{venue_id}").

        Returns:
            dict with: timestamp, signature, api_key, cloud_name, folder,
                        and the upload_url the frontend should POST to.
        """
        timestamp = int(time.time())

        params_to_sign = {
            "timestamp": timestamp,
            "folder": folder,
            "allowed_formats": "jpg,jpeg,png,webp",
            "max_file_size": 10_000_000,  # 10 MB
            "transformation": "c_limit,w_1920,h_1080,q_auto,f_auto",
            **kwargs,
        }

        signature = cloudinary.utils.api_sign_request(
            params_to_sign,
            settings.CLOUDINARY_API_SECRET,
        )

        return {
            "timestamp": timestamp,
            "signature": signature,
            "api_key": settings.CLOUDINARY_API_KEY,
            "cloud_name": settings.CLOUDINARY_CLOUD_NAME,
            "folder": folder,
            "allowed_formats": "jpg,jpeg,png,webp",
            "max_file_size": 10_000_000,
            "transformation": "c_limit,w_1920,h_1080,q_auto,f_auto",
            "upload_url": f"https://api.cloudinary.com/v1_1/{settings.CLOUDINARY_CLOUD_NAME}/image/upload",
        }

    def delete_file(self, public_id: str) -> bool:
        """
        Delete an image from Cloudinary using its public_id.

        Args:
            public_id: Cloudinary's unique identifier (e.g., "venues/abc123/image_xyz").

        Returns:
            True if successfully deleted, False otherwise.
        """
        try:
            result = cloudinary.uploader.destroy(public_id)
            success = result.get("result") == "ok"
            if success:
                logger.info("Deleted Cloudinary asset: %s", public_id)
            else:
                logger.warning("Cloudinary deletion returned: %s for %s", result, public_id)
            return success
        except Exception:
            logger.exception("Failed to delete Cloudinary asset: %s", public_id)
            return False
