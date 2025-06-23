"""Game schemas package."""

from .character import (
    ability_schema,
    spell_slots_schema,
    magic_schema,
    spell_effects_schema,
    character_schema,
    monster_schema
)

from .game_state import game_state_schema

from .actions import (
    action_schema,
    round_schema,
    response_schema,
    response_and_state_schema
)

from .locations import game_map_schema

__all__ = [
    # Character schemas
    'ability_schema',
    'spell_slots_schema',
    'magic_schema',
    'spell_effects_schema',
    'character_schema',
    'monster_schema',
    
    # Game state schema
    'game_state_schema',
    
    # Action schemas
    'action_schema',
    'round_schema',
    'response_schema',

    'game_map_schema'
]
