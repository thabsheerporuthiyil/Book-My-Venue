"""
AWS S3 Storage Backend (Stub).

This backend will be implemented when migrating from Cloudinary to S3.
It will use boto3 to generate presigned POST URLs for client-side uploads
and delete objects from S3 buckets.

To activate:
  1. pip install boto3
  2. Add AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET_NAME to .env
  3. Set STORAGE_BACKEND=apps.common.storage.s3_backend.S3StorageBackend
"""

from .base import BaseStorageBackend


class S3StorageBackend(BaseStorageBackend):
    """Future AWS S3 storage backend using presigned POST URLs."""

    def generate_signed_upload_params(self, folder: str, **kwargs) -> dict:
        """
        Generate S3 presigned POST parameters for client-side uploads.

        Implementation will use:
            boto3.client('s3').generate_presigned_post(
                Bucket=settings.AWS_S3_BUCKET_NAME,
                Key=f"{folder}/{uuid4()}.jpg",
                ExpiresIn=300,
            )
        """
        raise NotImplementedError(
            "S3 backend is not yet implemented. "
            "Set STORAGE_BACKEND to CloudinaryStorageBackend or implement this class."
        )

    def delete_file(self, public_id: str) -> bool:
        """
        Delete an object from S3.

        Implementation will use:
            boto3.client('s3').delete_object(
                Bucket=settings.AWS_S3_BUCKET_NAME,
                Key=public_id,
            )
        """
        raise NotImplementedError(
            "S3 backend is not yet implemented. "
            "Set STORAGE_BACKEND to CloudinaryStorageBackend or implement this class."
        )
