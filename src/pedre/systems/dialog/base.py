"""Base class for DialogManager."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from pedre.systems.base import BaseSystem


@dataclass
class DialogPage:
    """Represents a single page of dialog.

    Dialog can span multiple pages, with each page shown sequentially as the
    player advances through them. This class holds the data for one page,
    including metadata for tracking position within the full conversation.

    NPCs can have multiple dialog levels (0, 1, 2, etc.) that progress as the
    story unfolds. Each dialog level can contain multiple pages. For example:
    - Level 0: Initial greeting (2 pages)
    - Level 1: After completing a task (1 page)
    - Level 2: Final conversation (3 pages)

    Attributes:
        npc_name: Display name of the character speaking.
        text: The dialog text to display on this page.
        page_num: Zero-based index of this page in the full dialog.
        total_pages: Total number of pages in this dialog sequence.

    Example:
        # Page 2 of a 3-page dialog from Martin
        page = DialogPage(
            npc_name="Martin",
            text="This is the second page of dialog.",
            page_num=1,  # Zero-indexed
            total_pages=3
        )
        # Displays: "Martin" at top, "Page 2/3" at bottom
    """

    npc_name: str
    text: str
    page_num: int
    total_pages: int


class DialogBaseManager(BaseSystem, ABC):
    """Base class for DialogManager."""

    role = "dialog_manager"

    @abstractmethod
    def show_dialog(
        self,
        npc_name: str,
        text: list[str],
        *,
        instant: bool = False,
        auto_close: bool | None = None,
        dialog_level: int | None = None,
        npc_key: str | None = None,
    ) -> None:
        """Show a dialog from an NPC."""
        ...

    @abstractmethod
    def set_current_dialog_level(self, dialog_level: int) -> None:
        """Set current dialog level."""
        ...

    @abstractmethod
    def set_current_npc_name(self, npc_name: str) -> None:
        """Set current dialog level."""
        ...

    @abstractmethod
    def is_showing(self) -> bool:
        """Verify if dialog is showing."""
        ...
