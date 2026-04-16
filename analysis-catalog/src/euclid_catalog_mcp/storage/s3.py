"""S3 storage backend."""

import io
import os
import sys
import tempfile
from typing import BinaryIO, List, Dict, Any
from urllib.parse import urlparse

from .base import StorageBackend


class S3SeekableStream:
    """Seekable stream wrapper for S3 objects using Range requests."""

    def __init__(self, s3_client, bucket: str, key: str, size: int):
        """Initialize seekable stream.

        Args:
            s3_client: boto3 S3 client
            bucket: S3 bucket name
            key: S3 object key
            size: Total size of the object
        """
        self.s3_client = s3_client
        self.bucket = bucket
        self.key = key
        self.size = size
        self.position = 0
        self.buffer = b""
        self.buffer_start = 0

    def read(self, size: int = -1) -> bytes:
        """Read bytes from S3 object using Range requests."""
        # Check if we're at or past EOF
        if self.position >= self.size:
            return b""

        if size == -1:
            size = self.size - self.position

        if size <= 0:
            return b""

        # Don't read past EOF
        size = min(size, self.size - self.position)

        # Check if we need to fetch more data
        buffer_end = self.buffer_start + len(self.buffer)
        if self.position < self.buffer_start or self.position >= buffer_end:
            # Need to fetch new data
            chunk_size = max(size, 1024 * 1024)  # At least 1MB chunks
            end_byte = min(self.position + chunk_size - 1, self.size - 1)

            # Validate range before making request
            if self.position > self.size - 1:
                return b""

            response = self.s3_client.get_object(
                Bucket=self.bucket,
                Key=self.key,
                Range=f"bytes={self.position}-{end_byte}",
            )
            self.buffer = response["Body"].read()
            self.buffer_start = self.position

        # Read from buffer
        offset = self.position - self.buffer_start
        data = self.buffer[offset : offset + size]
        self.position += len(data)
        return data

    def seek(self, offset: int, whence: int = 0) -> int:
        """Seek to position in S3 object."""
        if whence == 0:  # absolute
            self.position = offset
        elif whence == 1:  # relative
            self.position += offset
        elif whence == 2:  # from end
            self.position = self.size + offset

        self.position = max(0, min(self.position, self.size))
        return self.position

    def tell(self) -> int:
        """Return current position."""
        return self.position

    def close(self):
        """Close stream."""
        self.buffer = b""


class S3Storage(StorageBackend):
    """S3 storage implementation."""

    def __init__(self):
        """Initialize S3 storage with boto3."""
        try:
            import boto3
            from botocore.config import Config

            # Read S3 configuration from environment variables
            endpoint_url = os.getenv("AWS_ENDPOINT_URL")
            verify_ssl = os.getenv("AWS_VERIFY_SSL", "true").lower() in (
                "true",
                "1",
                "yes",
            )
            use_streaming = os.getenv("S3_USE_STREAMING", "true").lower() in (
                "true",
                "1",
                "yes",
            )

            # Create S3 client with optional endpoint URL and SSL verification
            client_kwargs = {}
            if endpoint_url:
                client_kwargs["endpoint_url"] = endpoint_url

            # Configure SSL verification
            client_kwargs["verify"] = verify_ssl

            self.s3_client = boto3.client("s3", **client_kwargs)
            self.use_streaming = use_streaming

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
        """Open S3 object as seekable stream using Range requests.

        Uses HTTP Range requests to read only the needed parts of the file,
        avoiding downloading the entire file.
        """
        bucket, key = self.parse_s3_path(path)

        try:
            # Get file size
            response = self.s3_client.head_object(Bucket=bucket, Key=key)
            file_size = response["ContentLength"]
            size_mb = file_size / (1024 * 1024)

            if self.use_streaming:
                print(
                    f"Opening S3 file as stream ({size_mb:.2f} MB) - no download needed",
                    file=sys.stderr,
                )
                return S3SeekableStream(self.s3_client, bucket, key, file_size)
            else:
                # Fallback: download entire file
                print(f"Downloading entire file ({size_mb:.2f} MB)", file=sys.stderr)
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
                        files.append(
                            {
                                "name": os.path.basename(key),
                                "path": key,
                                "size_mb": round(obj["Size"] / (1024 * 1024), 2),
                            }
                        )
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

    def read_fits_header_only(
        self, path: str, max_header_size: int = 10 * 1024 * 1024
    ) -> bytes:
        """Read only the header portion of a FITS file from S3.

        FITS headers are ASCII text with 80-byte records. This method reads
        only the beginning of the file (default 10MB) which contains all headers.

        Args:
            path: S3 path to FITS file
            max_header_size: Maximum bytes to read (default 10MB)

        Returns:
            Bytes containing FITS headers
        """
        bucket, key = self.parse_s3_path(path)

        try:
            # Get file size
            response = self.s3_client.head_object(Bucket=bucket, Key=key)
            file_size = response["ContentLength"]
            size_mb = file_size / (1024 * 1024)

            # Read only the header portion
            read_size = min(max_header_size, file_size)
            read_mb = read_size / (1024 * 1024)

            print(
                f"Reading FITS header from S3 ({read_mb:.2f} MB of {size_mb:.2f} MB total)",
                file=sys.stderr,
            )

            response = self.s3_client.get_object(
                Bucket=bucket, Key=key, Range=f"bytes=0-{read_size - 1}"
            )
            return response["Body"].read()

        except Exception as e:
            raise FileNotFoundError(f"Failed to read FITS header from {path}: {e}")
