"""Base classes for validators."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class ValidationResult:
    """Result of a validation operation.

    Attributes:
        errors: List of error messages found during validation
        item_count: Number of items validated (scripts, dialogs, maps, etc.)
        metadata: Additional metrics (actions count, conditions count, etc.)
    """

    errors: list[str]
    item_count: int
    metadata: dict[str, int]


class Validator(ABC):
    """Base class for all validators.

    Validators check game assets (scripts, dialogs, maps) for errors
    and return structured results with error messages and metadata.
    """

    def __init__(self, path: Path) -> None:
        """Initialize validator with a path to validate.

        Args:
            path: Path to file or directory to validate
        """
        self.path = path

    @abstractmethod
    def validate(self) -> ValidationResult:
        """Validate content at the configured path.

        Returns:
            ValidationResult with errors and metadata
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for this validator (e.g., 'Scripts', 'Dialogs')."""
