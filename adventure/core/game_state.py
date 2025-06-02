"""Game state management module."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime

from ..schemas import game_state_schema
from ..prompts import GAME_RULES, STATE_CHANGE_RULES

class GameState:
    """Manages the game state and state transitions."""
    
    def __init__(self, initial_state: Optional[Dict[str, Any]] = None) -> None:
        """Initialize game state with default values or optional initial state."""
        self._state: Dict[str, Any] = initial_state or {
            "player": {
                "Name": "",
                "Pronouns": "",
                "Race": "",
                "Class": "",
                "Level": 1,
                "XP": 0,
                "HP": 0,
                "Max HP": 0,
                "Status": "Normal",
                "Gold": 0,
                "AC": 10,
                "Abilities": {
                    "Strength": 10,
                    "Dexterity": 10,
                    "Constitution": 10,
                    "Intelligence": 10,
                    "Wisdom": 10,
                    "Charisma": 10
                },
                "Proficiencies": {
                    "Skills": [],
                    "Weapons": [],
                    "Saving Throws": []
                },
                "Magic": {
                    "Spells Known": [],
                    "Cantrips Known": [],
                    "Spell Slots": []
                },
                "Spell Effects": [],
                "Inventory": []
            },
            "location": "",
            "danger": "safe",
            "time_of_day": "12:00",
            "sunrise": "06:00",
            "sunset": "18:00",
            "date": "",
            "dark": False,
            "monsters": [],
            "NPCs": []
        }
        self._context: List[Tuple[str, str]] = []
    
    @property
    def current_state(self) -> Dict[str, Any]:
        """Get the current game state."""
        return self._state
    
    @property
    def context(self) -> List[Tuple[str, str]]:
        """Get the conversation context."""
        return self._context
    
    def update(self, new_state: Dict[str, Any]) -> None:
        """Update the game state with new values."""
        # Validate new state
        if "player" in new_state and not isinstance(new_state["player"], dict):
            raise ValueError("Player data must be a dictionary")
        if "location" in new_state and not isinstance(new_state["location"], str):
            raise ValueError("Location must be a string")
        if "danger" in new_state and new_state["danger"] not in ["safe", "low", "medium", "high", "very high"]:
            logging.error(f"Invalid danger level: {new_state['danger']}")
            raise ValueError("Invalid danger level")
        
        self._state = new_state
    
    def add_to_context(self, speaker: str, message: str) -> None:
        """Add a message to the conversation context."""
        self._context.append((speaker, message))
    
    def clear_context(self) -> None:
        """Clear the conversation context."""
        self._context.clear()
    
    def save(self, filename: str) -> None:
        """Save the current game state to a file."""
        data = {
            "state": self._state,
            "context": self._context
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self, filename: str) -> None:
        """Load game state from a file."""
        with open(filename, 'r') as f:
            data = json.load(f)
        self._state = data["state"]
        self._context = data["context"]
    
    def is_player_dead(self) -> bool:
        """Check if the player is dead."""
        return self._state["player"]["Status"] == "Dead"
    
    def get_player_status(self) -> str:
        """Get the player's current status."""
        return self._state["player"]["Status"]
    
    def is_dark(self) -> bool:
        """Check if the current location is dark."""
        return self._state["dark"]
    
    def get_danger_level(self) -> str:
        """Get the current danger level."""
        return self._state["danger"]
    
    def get_location(self) -> str:
        """Get the current location."""
        return self._state["location"]
    
    def get_time_of_day(self) -> str:
        """Get the current time of day."""
        return self._state["time_of_day"]
    
    def get_date(self) -> str:
        """Get the current date."""
        return self._state["date"]
    
    def has_monsters(self) -> bool:
        """Check if there are monsters in the current location."""
        return len(self._state["monsters"]) > 0
    
    def has_npcs(self) -> bool:
        """Check if there are NPCs in the current location."""
        return len(self._state["NPCs"]) > 0
    
    def get_monsters(self) -> List[Dict]:
        """Get the list of monsters in the current area.
        
        Returns:
            List of monster dictionaries.
        """
        return self._state["monsters"]
    
    def get_npcs(self) -> List[Dict]:
        """Get the list of NPCs in the current area.
        
        Returns:
            List of NPC dictionaries.
        """
        return self._state["NPCs"] 