"""S3 storage backend."""

import io
import os
from typing import BinaryIO, List, Dict, Any
from urllib.parse import urlparse

from .base import StorageBackend


class S3Storage(StorageBackend):
    """S3 storage implementation."""

    def __init__(self):
        """Initialize S3 storage with boto3."""
        try:
            import boto3
            self.s3_client = boto3.client("s3")
        except ImportError:
            raise ImportError(
                "boto3 is required for S3 storage. Install with: pip install boto3"
            )

    def parse_s3_path(self, path: str) -> tuple[str, str]:
        """Parse S3 path into bucket and key.

        Args:
            path: S3 path (s3://bucket/key)

        Returns:
            Tuple of (bucket, key)
        """
        if not path.startswith("s3://"):
            raise ValueError(f"Invalid S3 path: {path}")

        parsed = urlparse(path)
        bucket = parsed.netloc
        key = parsed.path.lstrip("/")
        return bucket, key

    def exists(self, path: str) -> bool:
        """Check if S3 object exists."""
        try:
            bucket, key = self.parse_s3_path(path)
            self.s3_client.head_object(Bucket=bucket, Key=key)
            return True
        except Exception:
            return False

    def open(self, path: str) -> BinaryIO:
        """Download S3 object to memory and return file-like object."""
        bucket, key = self.parse_s3_path(path)

        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            content = response["Body"].read()
            return io.BytesIO(content)
        except Exception as e:
            raise FileNotFoundError(f"Failed to read S3 object {path}: {e}")

    def list_files(self, path: str, pattern: str = "*.fits") -> List[Dict[str, Any]]:
        """List S3 objects matching pattern."""
        bucket, prefix = self.parse_s3_path(path)

        # Convert glob pattern to simple suffix check
        suffix = pattern.replace("*", "")

        files = []
        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                if "Contents" not in page:
                    continue

                for obj in page["Contents"]:
                    key = obj["Key"]
                    if key.endswith(suffix):
                        files.append({
                            "name": os.path.basename(key),
                            "path": key,
                            "size_mb": round(obj["Size"] / (1024 * 1024), 2),
                        })
        except Exception as e:
            raise RuntimeError(f"Failed to list S3 objects: {e}")

        return files

    def get_size(self, path: str) -> int:
        """Get S3 object size in bytes."""
        bucket, key = self.parse_s3_path(path)

        try:
            response = self.s3_client.head_object(Bucket=bucket, Key=key)
            return response["ContentLength"]
        except Exception as e:
            raise FileNotFoundError(f"Failed to get S3 object size {path}: {e}")
