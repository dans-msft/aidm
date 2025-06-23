""" Schemas related to locations and the game map """

# Schema for a path between locations
path_schema = {
    "type": "object",
    "properties": {
        "direction": {"type": "string"},
        "destination": {"type": "string"},
        "description": {"type": "string"},
        "distance": {"type": "string"},
        "DM_notes": {"type": "string"}
    },
    "required": ["direction", "destination", "description", "distance", "DM_notes"],
    "additionalProperties": False
}

# Schema for a specific location
location_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "type": {"type": "string"},
        "description": {"type": "string"},
        "DM_notes": {"type": "string"},
        "paths": {"type": "array", "items": path_schema},
        "items": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["name", "type", "description", "DM_notes", "paths", "items"],
    "additionalProperties": False
}

region_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "DM_notes": {"type": "string"},
        "locations": {"type": "array", "items": location_schema}
    },
    "required": ["name", "description", "DM_notes", "locations"],
    "additionalProperties": False
}

# Schema for the overall game map
game_map_schema = {
    "type": "object",
    "properties": {
        "regions": {"type": "array", "items": region_schema}
    },
    "required": ["regions"],
    "additionalProperties": False
}