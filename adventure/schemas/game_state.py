"""Game state JSON schemas."""

from .character import character_schema, monster_schema

# Game state schema
game_state_schema = {
    "type": "object",
    "properties": {
        "player": character_schema,
        "location": {"type": "string"},
        "danger": {
            "type": "string",
            "enum": ["safe", "low", "medium", "high", "very high"]
        },
        "time_of_day": {"type": "string"},
        "sunrise": {"type": "string"},
        "sunset": {"type": "string"},
        "date": {"type": "string"},
        "dark": {"type": "boolean"},
        "monsters": {
            "type": "array",
            "items": monster_schema
        },
        "NPCs": {
            "type": "array",
            "items": character_schema
        }
    },
    "required": [
        "player", "location", "danger", "time_of_day", "sunrise", "sunset",
        "date", "dark", "monsters", "NPCs"
    ],
    "additionalProperties": False
} 