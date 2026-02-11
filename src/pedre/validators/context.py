"""Validation context for cross-referencing between asset types."""

from dataclasses import dataclass, field


@dataclass
class ValidationContext:
    """Shared context for cross-referencing validation between asset types.

    This context is populated during Phase 1 (structural validation) by each validator
    and then used during Phase 2 (cross-reference validation) to verify that references
    between different asset types are valid.

    For example:
    - Dialog files reference NPC names that should exist in maps
    - Scripts reference waypoints and NPCs that should exist in maps
    """

    map_entities: dict[str, dict[str, set[str]]] = field(default_factory=dict)

    dialog_npcs: dict[str, set[str]] = field(default_factory=dict)

    script_references: dict[str, dict[str, set[str]]] = field(default_factory=dict)

    def add_map_entity(self, map_name: str, entity_type: str, entity_name: str) -> None:
        """Register an entity found in a map.

        Args:
            map_name: Name of the map (without .tmx extension)
            entity_type: Type of entity (e.g., "npcs", "waypoints", "portals")
            entity_name: Name of the entity
        """
        if map_name not in self.map_entities:
            self.map_entities[map_name] = {}
        if entity_type not in self.map_entities[map_name]:
            self.map_entities[map_name][entity_type] = set()
        self.map_entities[map_name][entity_type].add(entity_name)

    def get_map_npcs(self, map_name: str) -> set[str]:
        """Get all NPC names in a specific map.

        Args:
            map_name: Name of the map (without .tmx extension)

        Returns:
            Set of NPC names in the map, or empty set if map not found
        """
        return self.map_entities.get(map_name, {}).get("npcs", set())

    def get_map_waypoints(self, map_name: str) -> set[str]:
        """Get all waypoint names in a specific map.

        Args:
            map_name: Name of the map (without .tmx extension)

        Returns:
            Set of waypoint names in the map, or empty set if map not found
        """
        return self.map_entities.get(map_name, {}).get("waypoints", set())

    def get_map_portals(self, map_name: str) -> set[str]:
        """Get all portal names in a specific map.

        Args:
            map_name: Name of the map (without .tmx extension)

        Returns:
            Set of portal names in the map, or empty set if map not found
        """
        return self.map_entities.get(map_name, {}).get("portals", set())

    def get_all_npcs(self) -> set[str]:
        """Get all NPC names across all maps.

        Returns:
            Set of all NPC names found in any map
        """
        all_npcs = set()
        for map_data in self.map_entities.values():
            all_npcs.update(map_data.get("npcs", set()))
        return all_npcs

    def get_all_waypoints(self) -> set[str]:
        """Get all waypoint names across all maps.

        Returns:
            Set of all waypoint names found in any map
        """
        all_waypoints = set()
        for map_data in self.map_entities.values():
            all_waypoints.update(map_data.get("waypoints", set()))
        return all_waypoints

    def get_all_portals(self) -> set[str]:
        """Get all portal names across all maps.

        Returns:
            Set of all portal names found in any map
        """
        all_portals = set()
        for map_data in self.map_entities.values():
            all_portals.update(map_data.get("portals", set()))
        return all_portals
