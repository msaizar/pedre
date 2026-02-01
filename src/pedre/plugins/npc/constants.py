"""Constants for NPC plugin."""

from pedre.sprites.constants import BASE_ANIMATION_PROPERTIES

# NPC-specific special animation properties
NPC_SPECIAL_ANIMATION_PROPERTIES = [
    "appear_frames",
    "appear_row",
    "disappear_frames",
    "disappear_row",
    "interact_up_frames",
    "interact_up_row",
    "interact_down_frames",
    "interact_down_row",
    "interact_left_frames",
    "interact_left_row",
    "interact_right_frames",
    "interact_right_row",
]

# All animation properties for NPCs (base + special)
ALL_ANIMATION_PROPERTIES = BASE_ANIMATION_PROPERTIES + NPC_SPECIAL_ANIMATION_PROPERTIES
