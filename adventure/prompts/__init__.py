"""Game prompts package."""

from .game_rules import GAME_RULES
from .response_rules import RESPONSE_RULES, STATE_CHANGE_RULES, RESPONSE_AND_STATE_CHANGE_RULES
from .action_rules import (
    ACTION_RULES,
    DEATH_RULES,
    SELF_PLAY_PROMPT
)
from .character_rules import CHARACTER_RULES

__all__ = [
    # Core game rules
    'GAME_RULES',
    
    # Response and state rules
    'RESPONSE_RULES',
    'STATE_CHANGE_RULES',
    
    # Action and character rules
    'ACTION_RULES',
    'CHARACTER_RULES',
    'DEATH_RULES',
    'SELF_PLAY_PROMPT'
]
