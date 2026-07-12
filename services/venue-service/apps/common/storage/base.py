"""
Abstract Storage Backend (Strategy Pattern).

All storage backends (Cloudinary, S3, GCS) must implement this interface.
To switch from Cloudinary to S3, simply:
  1. Implement S3StorageBackend (already stubbed).
  2. Change one setting: STORAGE_BACKEND = "apps.common.storage.s3_backend.S3StorageBackend"
  3. Redeploy.

Zero application code changes required.
"""

from abc import ABC, abstractmethod
from importlib import import_module


class BaseStorageBackend(ABC):
    """Interface that all storage backends must implement."""

    @abstractmethod
    def generate_signed_upload_params(self, folder: str, **kwargs) -> dict:
        """
        Generate signed parameters for client-side (browser) uploads.

        Returns a dict containing everything the frontend needs to upload
        directly to the storage provider (e.g., Cloudinary signature,
        S3 presigned POST URL).
        """

    @abstractmethod
    def delete_file(self, public_id: str) -> bool:
        """
        Delete a file from the storage provider.

        Args:
            public_id: The provider-specific identifier for the file.

        Returns:
            True if deletion was successful, False otherwise.
        """


def get_storage_backend() -> BaseStorageBackend:
    """
    Factory function that returns the configured storage backend instance.

    Reads the dotted path from settings.STORAGE_BACKEND, imports the class,
    and returns an instance.
    """
    from django.conf import settings

    backend_path = settings.STORAGE_BACKEND
    module_path, class_name = backend_path.rsplit(".", 1)
    module = import_module(module_path)
    backend_class = getattr(module, class_name)
    return backend_class()
