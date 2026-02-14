"""Abstract base class for storage backends."""

from abc import ABC, abstractmethod
from typing import BinaryIO, List, Dict, Any


class StorageBackend(ABC):
    """Abstract interface for file storage backends."""

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Check if file exists.

        Args:
            path: File path

        Returns:
            True if file exists
        """
        pass

    @abstractmethod
    def open(self, path: str) -> BinaryIO:
        """Open file for reading.

        Args:
            path: File path

        Returns:
            Binary file-like object
        """
        pass

    @abstractmethod
    def list_files(self, path: str, pattern: str = "*.fits") -> List[Dict[str, Any]]:
        """List files matching pattern.

        Args:
            path: Directory path
            pattern: File pattern (e.g., "*.fits")

        Returns:
            List of file info dictionaries
        """
        pass

    @abstractmethod
    def get_size(self, path: str) -> int:
        """Get file size in bytes.

        Args:
            path: File path

        Returns:
            File size in bytes
        """
        pass
