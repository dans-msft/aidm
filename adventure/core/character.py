"""Character management module."""

import json
import logging
from typing import Any, Dict, List, Optional, Union
from adventure.llm.client import LLMClient
from adventure.core.game_state import GameState

from ..schemas import character_schema
from ..prompts import CHARACTER_RULES

logger = logging.getLogger(__name__)

class CharacterManager:
    """Manages character creation and updates."""
    
    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize the character manager.
        
        Args:
            llm_client: The LLM client to use for character creation.
        """
        self.llm_client = llm_client
    
    def create_character(self, description: str) -> Dict[str, Any]:
        """Create a new character from a description.
        
        Args:
            description: A description of the character to create.
            
        Returns:
            A dictionary containing the character's attributes.
            
        Raises:
            ValueError: If the LLM response is invalid.
        """
        response = self.llm_client.make_structured_request(
            description,
            system_prompt=CHARACTER_RULES,
            schema=character_schema,
            name='character',
            use_detailed_model=True
        )
        
        return response
    
    def update_character(self, game_state: GameState, updates: Dict[str, Any]) -> None:
        """Update a character's attributes.
        
        Args:
            game_state: The game state containing the character to update.
            updates: A dictionary of attributes to update.
            
        Raises:
            ValueError: If the updates are invalid.
        """
        # Validate updates
        if not isinstance(updates, dict):
            raise ValueError("Updates must be a dictionary")
        
        # Update basic attributes
        for key, value in updates.items():
            if key in ["HP", "Max HP", "Gold", "Status", "AC"]:
                if not isinstance(value, (int, str)):
                    raise ValueError(f"Invalid value type for {key}")
                game_state.current_state["player"][key] = value
        
        # Update abilities
        if "Abilities" in updates:
            if not isinstance(updates["Abilities"], dict):
                raise ValueError("Abilities must be a dictionary")
            for ability, value in updates["Abilities"].items():
                if not isinstance(value, int) or value < 1 or value > 20:
                    raise ValueError(f"Invalid ability score for {ability}")
                game_state.current_state["player"]["Abilities"][ability] = value
        
        # Update proficiencies
        if "Proficiencies" in updates:
            if not isinstance(updates["Proficiencies"], dict):
                raise ValueError("Proficiencies must be a dictionary")
            for category, items in updates["Proficiencies"].items():
                if not isinstance(items, list):
                    raise ValueError(f"Proficiency {category} must be a list")
                game_state.current_state["player"]["Proficiencies"][category] = items
    
    def apply_damage(self, game_state: GameState, amount: int) -> None:
        """Apply damage to a character.
        
        Args:
            game_state: The game state containing the character.
            amount: The amount of damage to apply (negative for healing).
            
        Raises:
            ValueError: If the damage amount is invalid.
        """
        if not isinstance(amount, int):
            raise ValueError("Damage amount must be an integer")
        
        current_hp = game_state.current_state["player"]["HP"]
        new_hp = max(0, current_hp - amount)
        
        game_state.current_state["player"]["HP"] = new_hp
        
        # Update status based on HP
        if new_hp == 0:
            game_state.current_state["player"]["Status"] = "Dead"
        elif new_hp < current_hp:
            game_state.current_state["player"]["Status"] = "Injured"
        else:
            game_state.current_state["player"]["Status"] = "Normal"
    
    def apply_healing(self, game_state: GameState, amount: int) -> None:
        """Apply healing to a character.
        
        Args:
            game_state: The game state containing the character.
            amount: The amount of healing to apply.
            
        Raises:
            ValueError: If the healing amount is invalid.
        """
        if not isinstance(amount, int) or amount < 0:
            raise ValueError("Healing amount must be a non-negative integer")
        
        current_hp = game_state.current_state["player"]["HP"]
        max_hp = game_state.current_state["player"]["Max HP"]
        new_hp = min(max_hp, current_hp + amount)
        
        game_state.current_state["player"]["HP"] = new_hp
        
        # Update status based on HP
        if new_hp == 0:
            game_state.current_state["player"]["Status"] = "Dead"
        elif new_hp < max_hp:
            game_state.current_state["player"]["Status"] = "Injured"
        else:
            game_state.current_state["player"]["Status"] = "Normal"
    
    def update_spell_slots(
        self,
        game_state: GameState,
        updates: Dict[str, int],
        recover: bool = False
    ) -> None:
        """Update a character's spell slots.
        
        Args:
            game_state: The game state containing the character.
            updates: A dictionary mapping spell levels to slot changes.
            recover: Whether to recover used slots instead of adding new ones.
            
        Raises:
            ValueError: If the updates are invalid.
        """
        if not isinstance(updates, dict):
            raise ValueError("Updates must be a dictionary")
        
        slots = game_state.current_state["player"]["Magic"]["Spell Slots"]
        
        for level, change in updates.items():
            if not isinstance(change, int):
                raise ValueError(f"Invalid change for {level} level slots")
            
            # Find existing slot entry
            slot_entry = next(
                (slot for slot in slots if slot["level"] == int(level[0])),
                None
            )
            
            if slot_entry is None:
                if change < 0:
                    raise ValueError(f"Cannot use non-existent {level} level slots")
                slots.append({
                    "level": int(level[0]),
                    "total": change,
                    "used": 0
                })
            else:
                if recover:
                    slot_entry["used"] = max(0, slot_entry["used"] + change)
                else:
                    slot_entry["total"] = max(0, slot_entry["total"] + change)
                    slot_entry["used"] = max(0, slot_entry["used"] + change)
    
    def add_spell_effect(self, game_state: GameState, name: str, duration: int) -> None:
        """Add a spell effect to a character.
        
        Args:
            game_state: The game state containing the character.
            name: The name of the spell effect.
            duration: The duration of the effect in rounds.
            
        Raises:
            ValueError: If the parameters are invalid.
        """
        if not isinstance(name, str):
            raise ValueError("Spell effect name must be a string")
        if not isinstance(duration, int) or duration < 0:
            raise ValueError("Duration must be a non-negative integer")
        
        game_state.current_state["player"]["Spell Effects"].append({
            "name": name,
            "duration": duration
        })
    
    def update_spell_effects(self, game_state: GameState, rounds: int) -> None:
        """Update the remaining duration of spell effects.
        
        Args:
            game_state: The game state containing the character.
            rounds: The number of rounds that have passed.
            
        Raises:
            ValueError: If the number of rounds is invalid.
        """
        if not isinstance(rounds, int) or rounds < 0:
            raise ValueError("Rounds must be a non-negative integer")
        
        effects = game_state.current_state["player"]["Spell Effects"]
        remaining_effects = []
        
        for effect in effects:
            effect["duration"] -= rounds
            if effect["duration"] > 0:
                remaining_effects.append(effect)
        
        game_state.current_state["player"]["Spell Effects"] = remaining_effects 