"""Location management module."""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from ..schemas.locations import game_map_schema, region_schema, location_schema, path_schema

logger = logging.getLogger(__name__)

class LocationManager:
    """Manages the game world locations and player movement."""
    
    def __init__(self, world_map: Optional[Dict[str, Any]] = None, world_file: Optional[str] = None) -> None:
        """Initialize the location manager.
        
        Args:
            world_map: Optional initial world map data conforming to game_map_schema.
            world_file: Optional path to a world map JSON file to load.
                       If both world_map and world_file are provided, world_file takes precedence.
                       If neither is provided, an empty world map will be created.
        """
        # Dictionaries for fast lookups
        self._regions_by_name: Dict[str, Dict[str, Any]] = {}
        self._locations_by_name: Dict[str, Dict[str, Any]] = {}
        
        # Load world map from file if provided, otherwise use provided map or create empty
        if world_file:
            self.load_world_map(world_file)
        elif world_map:
            self._world_map = world_map
            self._validate_world_map()
            self._build_lookup_dictionaries()
        else:
            self._world_map = {"regions": []}
    
    def _build_lookup_dictionaries(self) -> None:
        """Build dictionaries for fast region and location lookups."""
        self._regions_by_name.clear()
        self._locations_by_name.clear()
        
        for region in self._world_map["regions"]:
            region_name = region["name"]
            if region_name in self._regions_by_name:
                raise ValueError(f"Duplicate region name found: {region_name}")
            self._regions_by_name[region_name] = region
            
            for location in region["locations"]:
                location_name = location["name"]
                if location_name in self._locations_by_name:
                    raise ValueError(f"Duplicate location name found: {location_name}")
                self._locations_by_name[location_name] = location
    
    def _validate_world_map(self) -> None:
        """Validate that the world map conforms to the schema.
        
        Raises:
            ValueError: If the world map is invalid.
        """
        # Basic validation of required fields
        if not isinstance(self._world_map, dict):
            raise ValueError("World map must be a dictionary")
        if "regions" not in self._world_map:
            raise ValueError("World map must contain 'regions' field")
        if not isinstance(self._world_map["regions"], list):
            raise ValueError("Regions must be a list")
        
        # Validate each region
        for region in self._world_map["regions"]:
            if not isinstance(region, dict):
                raise ValueError("Region must be a dictionary")
            for field in ["name", "description", "DM_notes", "locations"]:
                if field not in region:
                    raise ValueError(f"Region missing required field: {field}")
            if not isinstance(region["locations"], list):
                raise ValueError("Region locations must be a list")
            
            # Validate each location in the region
            for location in region["locations"]:
                if not isinstance(location, dict):
                    raise ValueError("Location must be a dictionary")
                for field in ["name", "type", "description", "DM_notes", "paths", "items"]:
                    if field not in location:
                        raise ValueError(f"Location missing required field: {field}")
                if not isinstance(location["paths"], list):
                    raise ValueError("Location paths must be a list")
                if not isinstance(location["items"], list):
                    raise ValueError("Location items must be a list")
                
                # Validate each path
                for path in location["paths"]:
                    if not isinstance(path, dict):
                        raise ValueError("Path must be a dictionary")
                    for field in ["direction", "destination", "description", "distance", "DM_notes"]:
                        if field not in path:
                            raise ValueError(f"Path missing required field: {field}")
    
    def load_world_map(self, filename: str) -> None:
        """Load a world map from a JSON file.
        
        Args:
            filename: Path to the JSON file containing the world map.
            
        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file contains invalid data.
        """
        try:
            with open(filename, 'r') as f:
                self._world_map = json.load(f)
            self._validate_world_map()
            self._build_lookup_dictionaries()
        except FileNotFoundError:
            raise FileNotFoundError(f"World map file not found: {filename}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in world map file: {filename}")
    
    def save_world_map(self, filename: str) -> None:
        """Save the current world map to a JSON file.
        
        Args:
            filename: Path where the world map should be saved.
            
        Raises:
            IOError: If the file cannot be written.
        """
        try:
            with open(filename, 'w') as f:
                json.dump(self._world_map, f, indent=2)
        except IOError as e:
            raise IOError(f"Failed to save world map: {e}")
    
    def get_location_info(self, location_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific location.
        
        Args:
            location_name: The name of the location to look up.
            
        Returns:
            A dictionary containing the location's information, or None if not found.
        """
        return self._locations_by_name.get(location_name)
    
    def get_region_info(self, region_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific region.
        
        Args:
            region_name: The name of the region to look up.
            
        Returns:
            A dictionary containing the region's information, or None if not found.
        """
        return self._regions_by_name.get(region_name)
    
    def get_available_paths(self, location_name: str) -> List[Dict[str, Any]]:
        """Get the available paths from a location.
        
        Args:
            location_name: The name of the location to check paths from.
        
        Returns:
            A list of path dictionaries, or empty list if location not found.
        """
        location = self.get_location_info(location_name)
        if location is None:
            return []
        return location["paths"]
    
    def can_move_to(self, from_location: str, to_location: str) -> bool:
        """Check if it's possible to move from one location to another.
        
        Args:
            from_location: The name of the starting location.
            to_location: The name of the destination location.
            
        Returns:
            True if there is a valid path from the starting location to the destination,
            False otherwise.
        """
        # Check if both locations exist
        from_loc = self.get_location_info(from_location)
        to_loc = self.get_location_info(to_location)
        if from_loc is None or to_loc is None:
            return False
        
        # Check if there's a path to the target location
        for path in from_loc["paths"]:
            if path["destination"] == to_location:
                return True
        
        return False
    
    def get_location_items(self, location_name: str) -> List[str]:
        """Get the items available at a location.
        
        Args:
            location_name: The name of the location to check items at.
        
        Returns:
            A list of item names, or empty list if location not found.
        """
        location = self.get_location_info(location_name)
        if location is None:
            return []
        return location["items"]
    
    def add_item_to_location(self, location_name: str, item: str) -> bool:
        """Add an item to a location.
        
        Args:
            location_name: The name of the location to add the item to.
            item: The name of the item to add.
            
        Returns:
            True if the item was added successfully, False if the location doesn't exist.
        """
        location = self.get_location_info(location_name)
        if location is None:
            return False
        
        if item not in location["items"]:
            location["items"].append(item)
        return True
    
    def remove_item_from_location(self, location_name: str, item: str) -> bool:
        """Remove an item from a location.
        
        Args:
            location_name: The name of the location to remove the item from.
            item: The name of the item to remove.
            
        Returns:
            True if the item was removed successfully, False if the location doesn't exist
            or the item wasn't there.
        """
        location = self.get_location_info(location_name)
        if location is None:
            return False
        
        if item in location["items"]:
            location["items"].remove(item)
            return True
        return False
    
    def get_all_locations(self) -> List[str]:
        """Get a list of all location names in the world.
        
        Returns:
            A list of all location names.
        """
        return list(self._locations_by_name.keys())
    
    def get_all_regions(self) -> List[str]:
        """Get a list of all region names in the world.
        
        Returns:
            A list of all region names.
        """
        return list(self._regions_by_name.keys())
    
    def get_locations_in_region(self, region_name: str) -> List[str]:
        """Get a list of all location names in a specific region.
        
        Args:
            region_name: The name of the region to get locations from.
            
        Returns:
            A list of location names in the region, or empty list if region not found.
        """
        region = self.get_region_info(region_name)
        if region is None:
            return []
        return [location["name"] for location in region["locations"]]
    
    def get_region_for_location(self, location_name: str) -> Optional[str]:
        """Get the name of the region containing a location.
        
        Args:
            location_name: The name of the location to find the region for.
            
        Returns:
            The name of the region containing the location, or None if the location
            doesn't exist.
        """
        location = self.get_location_info(location_name)
        if location is None:
            return None
            
        for region in self._world_map["regions"]:
            if location in region["locations"]:
                return region["name"]
        return None

    def get_immediate_context(self, current_location: str) -> Dict[str, Any]:
        """Get immediate context for the current location.
        
        Args:
            current_location: The name of the current location.
            
        Returns:
            Dictionary containing current location details, paths, and items.
        """
        location = self.get_location_info(current_location)
        if location is None:
            return {}
        
        return {
            "current_location": {
                "name": location["name"],
                "type": location["type"],
                "description": location["description"],
                "paths": location["paths"],
                "items": location["items"]
            }
        }

    def get_local_context(self, current_location: str, radius: int = 1) -> Dict[str, Any]:
        """Get local context including nearby locations within the specified radius.
        
        Args:
            current_location: The name of the current location.
            radius: Number of moves to include in the context (default: 1).
            
        Returns:
            Dictionary containing current location and nearby locations.
        """
        context = self.get_immediate_context(current_location)
        if not context:
            return {}
        
        # Get adjacent locations
        adjacent_locations = {}
        current_loc = self.get_location_info(current_location)
        if current_loc:
            for path in current_loc["paths"]:
                dest_name = path["destination"]
                dest_location = self.get_location_info(dest_name)
                if dest_location:
                    adjacent_locations[dest_name] = {
                        "name": dest_location["name"],
                        "type": dest_location["type"], 
                        "description": dest_location["description"],
                        "items": dest_location["items"],
                        "path_info": {
                            "direction": path["direction"],
                            "distance": path["distance"],
                            "description": path["description"]
                        }
                    }
        
        context["adjacent_locations"] = adjacent_locations
        return context

    def get_regional_context(self, current_location: str) -> Dict[str, Any]:
        """Get regional context including current region and neighboring regions.
        
        Args:
            current_location: The name of the current location.
            
        Returns:
            Dictionary containing regional information and neighboring regions.
        """
        region_name = self.get_region_for_location(current_location)
        if region_name is None:
            return {}
        
        current_region = self.get_region_info(region_name)
        if current_region is None:
            return {}
        
        # Find neighboring regions by looking at paths that cross region boundaries
        neighboring_regions = set()
        for location in current_region["locations"]:
            for path in location["paths"]:
                dest_region = self.get_region_for_location(path["destination"])
                if dest_region and dest_region != region_name:
                    neighboring_regions.add(dest_region)
        
        # Build neighboring region info
        neighbor_info = {}
        for neighbor_name in neighboring_regions:
            neighbor_region = self.get_region_info(neighbor_name)
            if neighbor_region:
                neighbor_info[neighbor_name] = {
                    "name": neighbor_region["name"],
                    "description": neighbor_region["description"]
                }
        
        return {
            "current_region": {
                "name": current_region["name"],
                "description": current_region["description"],
                "location_count": len(current_region["locations"])
            },
            "neighboring_regions": neighbor_info
        }

    def get_action_context(self, current_location: str) -> Dict[str, Any]:
        """Get context optimized for action resolution.
        
        Args:
            current_location: The name of the current location.
            
        Returns:
            Dictionary containing immediate and local context for action resolution.
        """
        return self.get_local_context(current_location, radius=1)

    def get_narrative_context(self, current_location: str) -> Dict[str, Any]:
        """Get context optimized for narrative generation.
        
        Args:
            current_location: The name of the current location.
            
        Returns:
            Dictionary containing immediate, local, and regional context for storytelling.
        """
        context = self.get_local_context(current_location, radius=1)
        regional_context = self.get_regional_context(current_location)
        
        # Merge contexts
        context.update(regional_context)
        return context

    def get_exploration_context(self, current_location: str) -> Dict[str, Any]:
        """Get context optimized for exploration and movement.
        
        Args:
            current_location: The name of the current location.
            
        Returns:
            Dictionary containing paths, adjacent locations, and regional overview.
        """
        context = self.get_local_context(current_location, radius=2)
        regional_context = self.get_regional_context(current_location)
        
        # Add all available paths with more detail
        current_loc = self.get_location_info(current_location)
        if current_loc:
            detailed_paths = []
            for path in current_loc["paths"]:
                dest_location = self.get_location_info(path["destination"])
                path_detail = path.copy()
                if dest_location:
                    path_detail["destination_type"] = dest_location["type"]
                    path_detail["destination_region"] = self.get_region_for_location(path["destination"])
                detailed_paths.append(path_detail)
            context["detailed_paths"] = detailed_paths
        
        context.update(regional_context)
        return context

    def get_dm_context(self, current_location: str) -> Dict[str, Any]:
        """Get DM-specific context including hidden information.
        
        Args:
            current_location: The name of the current location.
            
        Returns:
            Dictionary containing DM notes and hidden information.
        """
        context = self.get_narrative_context(current_location)
        
        # Add DM-specific information
        current_loc = self.get_location_info(current_location)
        if current_loc:
            context["current_location"]["DM_notes"] = current_loc["DM_notes"]
            
            # Add DM notes for paths
            for path in context["current_location"]["paths"]:
                path["DM_notes"] = path["DM_notes"]
        
        # Add regional DM notes
        region_name = self.get_region_for_location(current_location)
        if region_name:
            region = self.get_region_info(region_name)
            if region:
                context["current_region"]["DM_notes"] = region["DM_notes"]
        
        return context

    def format_context_for_prompt(self, context: Dict[str, Any], include_dm_notes: bool = False) -> str:
        """Format world context for inclusion in LLM prompts.
        
        Args:
            context: World context dictionary from one of the get_*_context methods.
            include_dm_notes: Whether to include DM notes in the formatted output.
            
        Returns:
            Formatted string suitable for inclusion in LLM prompts.
        """
        if not context:
            return "No world context available."
        
        lines = ["## World Context"]
        
        # Current location
        if "current_location" in context:
            loc = context["current_location"]
            lines.append(f"### Current Location: {loc['name']}")
            lines.append(f"Type: {loc['type']}")
            lines.append(f"Description: {loc['description']}")
            
            if include_dm_notes and "DM_notes" in loc:
                lines.append(f"DM Notes: {loc['DM_notes']}")
            
            if loc.get("items"):
                lines.append(f"Items present: {', '.join(loc['items'])}")
            
            if loc.get("paths"):
                lines.append("Available paths:")
                for path in loc["paths"]:
                    lines.append(f"  - {path['direction']}: {path['description']} (Distance: {path['distance']})")
                    if include_dm_notes and "DM_notes" in path:
                        lines.append(f"    DM Notes: {path['DM_notes']}")
        
        # Adjacent locations
        if "adjacent_locations" in context and context["adjacent_locations"]:
            lines.append("### Adjacent Locations:")
            for name, adj_loc in context["adjacent_locations"].items():
                path_info = adj_loc.get("path_info", {})
                lines.append(f"- {name} ({adj_loc['type']}): {adj_loc['description']}")
                if path_info:
                    lines.append(f"  Access: {path_info.get('direction', 'unknown')} - {path_info.get('distance', 'unknown distance')}")
                if adj_loc.get("items"):
                    lines.append(f"  Items: {', '.join(adj_loc['items'])}")
        
        # Regional context
        if "current_region" in context:
            region = context["current_region"]
            lines.append(f"### Current Region: {region['name']}")
            lines.append(f"Description: {region['description']}")
            if include_dm_notes and "DM_notes" in region:
                lines.append(f"DM Notes: {region['DM_notes']}")
        
        # Neighboring regions
        if "neighboring_regions" in context and context["neighboring_regions"]:
            lines.append("### Neighboring Regions:")
            for name, neighbor in context["neighboring_regions"].items():
                lines.append(f"- {name}: {neighbor['description']}")
        
        return "\n".join(lines)

    def get_world_overview(self) -> str:
        """Get a brief overview of all locations in the game world.
        
        Returns:
            Formatted string listing all regions and locations for initial game state.
        """
        if not self._world_map or not self._world_map.get("regions"):
            return "No world map available."
        
        lines = ["## World Overview"]
        
        for region in self._world_map["regions"]:
            lines.append(f"### {region['name']}")
            lines.append(f"{region['description']}")
            
            location_names = [loc['name'] for loc in region['locations']]
            lines.append(f"Locations: {', '.join(location_names)}")
            lines.append("")  # Empty line between regions
        
        return "\n".join(lines) 