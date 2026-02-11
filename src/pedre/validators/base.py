"""Base classes for validators."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from pedre.validators.context import ValidationContext


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

    Validation happens in two phases:
    1. Structural validation: Check individual assets for correctness
    2. Cross-reference validation: Check references between different asset types
    """

    def __init__(self, path: Path, context: ValidationContext) -> None:
        """Initialize validator with a path and validation context.

        Args:
            path: Path to file or directory to validate
            context: Shared context for cross-referencing validation
        """
        self.path = path
        self.context = context

    @abstractmethod
    def validate(self) -> ValidationResult:
        """Validate content at the configured path (Phase 1: Structural validation).

        This method should:
        1. Check the structure and correctness of individual assets
        2. Populate the context with entity information for cross-referencing

        Returns:
            ValidationResult with errors and metadata
        """

    @abstractmethod
    def validate_cross_references(self) -> ValidationResult:
        """Validate cross-references using populated context (Phase 2: Cross-reference validation).

        This method should check that references to other assets are valid.
        For example:
        - Dialog files reference NPCs that exist in maps
        - Scripts reference waypoints that exist in maps

        Returns:
            ValidationResult with cross-reference errors and metadata
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for this validator (e.g., 'Scripts', 'Dialogs')."""
