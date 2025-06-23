"""Action-related JSON schemas for the game."""

from .game_state import game_state_schema

# Action schema
action_schema = {
    "type": "object",
    "properties": {
        "action_type": {"type": "string"},
        "target": {"type": "string"},
        "how_to_resolve": {"type": "string"},
        "advantage": {"type": "boolean"},
        "disadvantage": {"type": "boolean"},
        "dice_to_roll": {"type": "string"},
        "number_to_beat": {"type": "integer"},
        "result_if_successful": {"type": "string"},
        "result_if_failed": {"type": "string"}
    },
    "required": [
        "action_type", "target", "how_to_resolve", "advantage", "disadvantage",
        "dice_to_roll", "number_to_beat", "result_if_successful", "result_if_failed"
    ],
    "additionalProperties": False
}

# Round schema (collection of actions)
round_schema = {
    "type": "object",
    "properties": {
        "actions": {
            "type": "array",
            "items": action_schema
        }
    },
    "required": ["actions"],
    "additionalProperties": False
}

# Response schema
response_schema = {
    "type": "object",
    "properties": {
        "player_response": {"type": "string"},
        "DM_response": {"type": "string"}
    },
    "required": ["player_response", "DM_response"],
    "additionalProperties": False
} 

# Response schema with embedded game state
response_and_state_schema = {
    "type": "object",
    "properties": {
        "player_response": {"type": "string"},
        "DM_response": {"type": "string"},
        "new_state": game_state_schema
    },
    "required": ["player_response", "DM_response", "new_state"],
    "additionalProperties": False
} 