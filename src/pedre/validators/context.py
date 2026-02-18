"""Validation context for cross-referencing between asset types."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pedre.types import EntityReference


@dataclass
class ValidationContext:
    """Shared context used during multi-phase validation.

    This context is populated during structural validation (Phase 1) by
    individual validators (maps, dialogs, scripts, etc.). It is then used
    during cross-reference validation (Phase 2) to verify that references
    between different asset types are valid.

    Example cross-references:
        - Dialog files referencing NPCs defined in maps
        - Scripts referencing waypoints, portals, or interactive objects
        - Scripts referencing NPCs defined in maps

    Attributes:
        map_entities:
            Nested mapping of:
                map_name -> entity_type -> set(entity_name)

    Example:
                {
                    "town": {
                        "npcs": {"bob", "alice"},
                        "waypoints": {"center"},
                    }
                }

        dialog_npcs:
            Mapping of dialog file name -> set of referenced NPC names.

        script_references:
            Mapping of script file name -> set of extracted EntityReference
            instances used during validation.
    """

    map_entities: dict[str, dict[str, set[str]]] = field(default_factory=dict)
    script_references: dict[str, set[EntityReference]] = field(default_factory=dict)
    dialog_references: dict[tuple[str, str, str], set[EntityReference]] = field(default_factory=dict)

    def add_map_entity(
        self,
        map_name: str,
        entity_type: str,
        entity_name: str,
    ) -> None:
        """Register an entity discovered in a map.

        Args:
            map_name: Name of the map (without file extension).
            entity_type: Type of entity (e.g. "npcs", "waypoints",
                "portals", "interactive_objects").
            entity_name: Name of the entity within the map.
        """
        self.map_entities.setdefault(map_name, {}).setdefault(entity_type, set()).add(entity_name)

    def _get_map_entities(self, map_name: str, entity_type: str) -> set[str]:
        """Return entities of a specific type for a given map.

        Args:
            map_name: Name of the map.
            entity_type: Type of entity to retrieve.

        Returns:
            Set of entity names, or an empty set if none exist.
        """
        return self.map_entities.get(map_name, {}).get(entity_type, set())

    def get_map_npcs(self, map_name: str) -> set[str]:
        """Return all NPC names defined in a specific map."""
        return self._get_map_entities(map_name, "npcs")

    def get_map_waypoints(self, map_name: str) -> set[str]:
        """Return all waypoint names defined in a specific map."""
        return self._get_map_entities(map_name, "waypoints")

    def get_map_portals(self, map_name: str) -> set[str]:
        """Return all portal names defined in a specific map."""
        return self._get_map_entities(map_name, "portals")

    def get_map_interactive_objects(self, map_name: str) -> set[str]:
        """Return all interactive object names defined in a specific map."""
        return self._get_map_entities(map_name, "interactive_objects")

    def _get_all_entities(self, entity_type: str) -> set[str]:
        """Aggregate entities of a given type across all maps.

        Args:
            entity_type: Type of entity to aggregate.

        Returns:
            Set of unique entity names found in any map.
        """
        return {name for map_data in self.map_entities.values() for name in map_data.get(entity_type, set())}

    def get_all_npcs(self) -> set[str]:
        """Return all NPC names defined across all maps."""
        return self._get_all_entities("npcs")

    def get_all_waypoints(self) -> set[str]:
        """Return all waypoint names defined across all maps."""
        return self._get_all_entities("waypoints")

    def get_all_portals(self) -> set[str]:
        """Return all portal names defined across all maps."""
        return self._get_all_entities("portals")

    def get_all_interactive_objects(self) -> set[str]:
        """Return all interactive object names defined across all maps."""
        return self._get_all_entities("interactive_objects")

    def get_all_maps(self) -> set[str]:
        """Return all known map names registered in the context."""
        return set(self.map_entities)
