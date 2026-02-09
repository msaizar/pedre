"""Actions for dialog plugin."""

import logging
from typing import TYPE_CHECKING, Any, Self

from pedre.actions import Action, WaitForConditionAction
from pedre.actions.registry import ActionRegistry
from pedre.conf import settings

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext

logger = logging.getLogger(__name__)


@ActionRegistry.register("dialog")
class DialogAction(Action):
    """Show a dialog to the player.

    This action displays a dialog box with text from a speaker. The dialog
    is handled by the dialog plugin and can consist of multiple pages that
    the player advances through.

    The action completes immediately after queuing the dialog - it doesn't
    wait for the player to finish reading. Use WaitForDialogCloseAction if
    you need to wait for the player to dismiss the dialog before proceeding.

    Example usage:
        {
            "type": "dialog",
            "speaker": "martin",
            "text": ["Hello there!", "Welcome to the game."]
        }

        # With instant display (no letter-by-letter reveal)
        {
            "type": "dialog",
            "speaker": "Narrator",
            "text": ["The world fades to black..."],
            "instant": true
        }

        # With auto-close for cutscenes
        {
            "type": "dialog",
            "speaker": "Narrator",
            "text": ["The adventure begins..."],
            "auto_close": true
        }
    """

    def __init__(
        self,
        speaker: str,
        text: list[str],
        *,
        instant: bool = settings.DIALOG_INSTANT_TEXT_DEFAULT,
        auto_close: bool = settings.DIALOG_AUTO_CLOSE_DEFAULT,
    ) -> None:
        """Initialize dialog action.

        Args:
            speaker: Name of the character speaking.
            text: List of dialog pages to show.
            instant: If True, text appears immediately without letter-by-letter reveal.
                Defaults to settings.DIALOG_INSTANT_TEXT_DEFAULT.
            auto_close: If True, dialog automatically closes after configured duration.
                If False, player must manually close. Defaults to settings.DIALOG_AUTO_CLOSE_DEFAULT.
        """
        self.speaker = speaker
        self.text = text
        self.instant = instant
        self.auto_close = auto_close
        self.started = False

    def execute(self, context: GameContext) -> bool:
        """Show dialog if not already showing."""
        if not self.started:
            dialog_plugin = context.dialog_plugin
            dialog_plugin.show_dialog(self.speaker, self.text, instant=self.instant, auto_close=self.auto_close)
            logger.debug("DialogAction: Showing dialog from %s", self.speaker)
            self.started = True

        # Action completes immediately, dialog plugin handles display
        return True

    def reset(self) -> None:
        """Reset the action."""
        self.started = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create DialogAction from a dictionary.

        Note: This handles basic dialog creation. For text_from references,
        the ScriptPlugin handles resolution before calling this method.
        """
        return cls(
            speaker=data.get("speaker", ""),
            text=data.get("text", []),
            instant=data.get("instant", settings.DIALOG_INSTANT_TEXT_DEFAULT),
            auto_close=data.get("auto_close", settings.DIALOG_AUTO_CLOSE_DEFAULT),
        )

    @classmethod
    def validate_params(cls, data: dict[str, Any]) -> list[str]:
        """Validate dialog action parameters.

        Returns:
            List of error messages. Empty list means valid.
        """
        errors = []
        text = data.get("text")
        if not text:
            errors.append("missing required 'text' field")
        elif not isinstance(text, list):
            errors.append("'text' must be a list")
        elif not all(isinstance(item, str) for item in text):
            errors.append("'text' items must be strings")

        speaker = data.get("speaker")
        if not speaker:
            errors.append("missing required 'speaker' field")
        elif not isinstance(speaker, str):
            errors.append("'speaker' must be a string")

        if "instant" in data and not isinstance(data["instant"], bool):
            errors.append("'instant' must be a bool")

        if "auto_close" in data and not isinstance(data["auto_close"], bool):
            errors.append("'auto_close' must be a bool")

        return errors


@ActionRegistry.register("wait_for_dialog_close")
class WaitForDialogCloseAction(WaitForConditionAction):
    """Wait for dialog to be closed.

    This action pauses script execution until the player dismisses the currently
    showing dialog. It's essential for creating proper dialog sequences where each
    message should be read before continuing.

    Commonly used after DialogAction to ensure the player has seen the message
    before the script proceeds to the next action.

    Example usage in a sequence:
        [
            {"type": "dialog", "speaker": "martin", "text": ["Hello!"]},
            {"type": "wait_for_dialog_close"},
            {"type": "dialog", "speaker": "yema", "text": ["Hi there!"]}
        ]
    """

    def __init__(self) -> None:
        """Initialize dialog wait action."""

        def check_dialog_closed(ctx: GameContext) -> bool:
            dialog_plugin = ctx.dialog_plugin
            return dialog_plugin is None or not dialog_plugin.is_showing()

        super().__init__(check_dialog_closed, "Dialog closed")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:  # noqa: ARG003
        """Create WaitForDialogCloseAction from a dictionary."""
        return cls()
