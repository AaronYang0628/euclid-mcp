"""Local filesystem storage backend."""

from pathlib import Path
from typing import BinaryIO, List, Dict, Any

from .base import StorageBackend


class LocalStorage(StorageBackend):
    """Local filesystem storage implementation."""

    def __init__(self, base_path: str = "/data/catalogs"):
        """Initialize local storage.

        Args:
            base_path: Base directory for relative paths
        """
        self.base_path = Path(base_path)

    def resolve_path(self, path: str) -> Path:
        """Resolve path relative to base_path if not absolute.

        Args:
            path: File path

        Returns:
            Resolved Path object
        """
        p = Path(path)
        if p.is_absolute():
            return p
        return self.base_path / path

    def exists(self, path: str) -> bool:
        """Check if file exists."""
        return self.resolve_path(path).exists()

    def open(self, path: str) -> BinaryIO:
        """Open file for reading."""
        resolved = self.resolve_path(path)
        if not resolved.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return open(resolved, "rb")

    def list_files(self, path: str, pattern: str = "*.fits") -> List[Dict[str, Any]]:
        """List files matching pattern."""
        resolved = self.resolve_path(path)
        if not resolved.exists():
            return []

        files = []
        for file_path in resolved.rglob(pattern):
            if file_path.is_file():
                relative = file_path.relative_to(resolved)
                files.append({
                    "name": file_path.name,
                    "path": str(relative),
                    "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
                })
        return files

    def get_size(self, path: str) -> int:
        """Get file size in bytes."""
        resolved = self.resolve_path(path)
        if not resolved.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return resolved.stat().st_size
