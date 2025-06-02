"""Tests for the character management module."""

import pytest  # type: ignore
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, cast

from adventure.core.character import CharacterManager
from adventure.core.game_state import GameState
from adventure.llm.client import LLMClient

@pytest.fixture
def mock_llm_client() -> MagicMock:
    """Create a mock LLM client."""
    client = MagicMock(spec=LLMClient)
    client.make_structured_request = AsyncMock()
    return client

@pytest.fixture
def mock_game_state() -> MagicMock:
    """Create a mock game state."""
    state = MagicMock(spec=GameState)
    state.current_state = {
        "player": {
            "Name": "Test Character",
            "Pronouns": "they/them",
            "Race": "Human",
            "Class": "Fighter",
            "Level": 1,
            "XP": 0,
            "HP": 10,
            "Max HP": 10,
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
                "Skills": ["Athletics"],
                "Weapons": ["Longsword"],
                "Saving Throws": ["Strength", "Constitution"]
            },
            "Magic": {
                "Spells Known": [],
                "Cantrips Known": [],
                "Spell Slots": []
            },
            "Spell Effects": [],
            "Inventory": []
        }
    }
    return state

@pytest.mark.asyncio
async def test_character_manager_initialization(mock_llm_client: MagicMock) -> None:
    """Test character manager initialization."""
    manager = CharacterManager(mock_llm_client)
    assert manager.llm_client == mock_llm_client

@pytest.mark.asyncio
async def test_create_character(mock_llm_client: MagicMock) -> None:
    """Test character creation."""
    manager = CharacterManager(mock_llm_client)
    
    # Mock LLM response
    mock_response = {
        "character": {
            "Name": "Test Character",
            "Pronouns": "they/them",
            "Race": "Human",
            "Class": "Fighter",
            "Level": 1,
            "XP": 0,
            "HP": 10,
            "Max HP": 10,
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
                "Skills": ["Athletics"],
                "Weapons": ["Longsword"],
                "Saving Throws": ["Strength", "Constitution"]
            },
            "Magic": {
                "Spells Known": [],
                "Cantrips Known": [],
                "Spell Slots": []
            },
            "Spell Effects": [],
            "Inventory": []
        }
    }
    mock_llm_client.make_structured_request.return_value = mock_response
    
    character = await manager.create_character("A human fighter")
    assert character == mock_response["character"]
    mock_llm_client.make_structured_request.assert_called_once()

@pytest.mark.asyncio
async def test_create_character_invalid_response(mock_llm_client: MagicMock) -> None:
    """Test character creation with invalid LLM response."""
    manager = CharacterManager(mock_llm_client)
    mock_llm_client.make_structured_request.return_value = {"invalid": "response"}
    
    with pytest.raises(ValueError, match="Invalid character creation response"):
        await manager.create_character("A human fighter")

def test_update_character(mock_game_state: MagicMock) -> None:
    """Test character updates."""
    manager = CharacterManager(MagicMock())
    
    # Test basic attribute updates
    updates = {
        "HP": 5,
        "Gold": 100,
        "Status": "Injured",
        "AC": 15
    }
    manager.update_character(mock_game_state, updates)
    assert mock_game_state.current_state["player"]["HP"] == 5
    assert mock_game_state.current_state["player"]["Gold"] == 100
    assert mock_game_state.current_state["player"]["Status"] == "Injured"
    assert mock_game_state.current_state["player"]["AC"] == 15
    
    # Test ability updates
    ability_updates = {
        "Abilities": {
            "Strength": 15,
            "Dexterity": 14
        }
    }
    manager.update_character(mock_game_state, ability_updates)
    assert mock_game_state.current_state["player"]["Abilities"]["Strength"] == 15
    assert mock_game_state.current_state["player"]["Abilities"]["Dexterity"] == 14
    
    # Test proficiency updates
    proficiency_updates = {
        "Proficiencies": {
            "Skills": ["Athletics", "Perception"],
            "Weapons": ["Longsword", "Shortbow"]
        }
    }
    manager.update_character(mock_game_state, proficiency_updates)
    assert mock_game_state.current_state["player"]["Proficiencies"]["Skills"] == ["Athletics", "Perception"]
    assert mock_game_state.current_state["player"]["Proficiencies"]["Weapons"] == ["Longsword", "Shortbow"]

def test_update_character_invalid_updates(mock_game_state: MagicMock) -> None:
    """Test character updates with invalid data."""
    manager = CharacterManager(MagicMock())
    
    with pytest.raises(ValueError, match="Updates must be a dictionary"):
        manager.update_character(mock_game_state, cast(Dict[str, Any], "invalid"))
    
    with pytest.raises(ValueError, match="Invalid value type for HP"):
        manager.update_character(mock_game_state, {"HP": cast(int, "invalid")})
    
    with pytest.raises(ValueError, match="Abilities must be a dictionary"):
        manager.update_character(mock_game_state, {"Abilities": cast(Dict[str, int], "invalid")})
    
    with pytest.raises(ValueError, match="Invalid ability score for Strength"):
        manager.update_character(mock_game_state, {"Abilities": {"Strength": 0}})
    
    with pytest.raises(ValueError, match="Proficiency Skills must be a list"):
        manager.update_character(mock_game_state, {"Proficiencies": {"Skills": cast(list, "invalid")}})

def test_apply_damage(mock_game_state: MagicMock) -> None:
    """Test damage application."""
    manager = CharacterManager(MagicMock())
    
    # Test normal damage
    manager.apply_damage(mock_game_state, 5)
    assert mock_game_state.current_state["player"]["HP"] == 5
    assert mock_game_state.current_state["player"]["Status"] == "Injured"
    
    # Test lethal damage
    manager.apply_damage(mock_game_state, 10)
    assert mock_game_state.current_state["player"]["HP"] == 0
    assert mock_game_state.current_state["player"]["Status"] == "Dead"
    
    # Test healing through negative damage
    manager.apply_damage(mock_game_state, -5)
    assert mock_game_state.current_state["player"]["HP"] == 5
    assert mock_game_state.current_state["player"]["Status"] == "Injured"

def test_apply_damage_invalid(mock_game_state: MagicMock) -> None:
    """Test damage application with invalid input."""
    manager = CharacterManager(MagicMock())
    
    with pytest.raises(ValueError, match="Damage amount must be an integer"):
        manager.apply_damage(mock_game_state, cast(int, "invalid"))

def test_apply_healing(mock_game_state: MagicMock) -> None:
    """Test healing application."""
    manager = CharacterManager(MagicMock())
    
    # Apply some damage first
    manager.apply_damage(mock_game_state, 5)
    assert mock_game_state.current_state["player"]["HP"] == 5
    
    # Test normal healing
    manager.apply_healing(mock_game_state, 3)
    assert mock_game_state.current_state["player"]["HP"] == 8
    assert mock_game_state.current_state["player"]["Status"] == "Injured"
    
    # Test overhealing
    manager.apply_healing(mock_game_state, 5)
    assert mock_game_state.current_state["player"]["HP"] == 10
    assert mock_game_state.current_state["player"]["Status"] == "Normal"

def test_apply_healing_invalid(mock_game_state: MagicMock) -> None:
    """Test healing application with invalid input."""
    manager = CharacterManager(MagicMock())
    
    with pytest.raises(ValueError, match="Healing amount must be a non-negative integer"):
        manager.apply_healing(mock_game_state, -1)
    
    with pytest.raises(ValueError, match="Healing amount must be a non-negative integer"):
        manager.apply_healing(mock_game_state, cast(int, "invalid"))

def test_update_spell_slots(mock_game_state: MagicMock) -> None:
    """Test spell slot updates."""
    manager = CharacterManager(MagicMock())
    
    # Test adding new slots
    updates = {"1st": 2, "2nd": 1}
    manager.update_spell_slots(mock_game_state, updates)
    slots = mock_game_state.current_state["player"]["Magic"]["Spell Slots"]
    assert len(slots) == 2
    assert slots[0]["level"] == 1
    assert slots[0]["total"] == 2
    assert slots[0]["used"] == 0
    assert slots[1]["level"] == 2
    assert slots[1]["total"] == 1
    assert slots[1]["used"] == 0
    
    # Test using slots
    updates = {"1st": -1}
    manager.update_spell_slots(mock_game_state, updates)
    assert slots[0]["used"] == 1
    
    # Test recovering slots
    updates = {"1st": 1}
    manager.update_spell_slots(mock_game_state, updates, recover=True)
    assert slots[0]["used"] == 0

def test_update_spell_slots_invalid(mock_game_state: MagicMock) -> None:
    """Test spell slot updates with invalid input."""
    manager = CharacterManager(MagicMock())
    
    with pytest.raises(ValueError, match="Updates must be a dictionary"):
        manager.update_spell_slots(mock_game_state, cast(Dict[str, int], "invalid"))
    
    with pytest.raises(ValueError, match="Invalid change for 1st level slots"):
        manager.update_spell_slots(mock_game_state, {"1st": cast(int, "invalid")})
    
    with pytest.raises(ValueError, match="Cannot use non-existent 1st level slots"):
        manager.update_spell_slots(mock_game_state, {"1st": -1})

def test_spell_effects(mock_game_state: MagicMock) -> None:
    """Test spell effect management."""
    manager = CharacterManager(MagicMock())
    
    # Test adding effects
    manager.add_spell_effect(mock_game_state, "Bless", 10)
    manager.add_spell_effect(mock_game_state, "Haste", 5)
    effects = mock_game_state.current_state["player"]["Spell Effects"]
    assert len(effects) == 2
    assert effects[0]["name"] == "Bless"
    assert effects[0]["duration"] == 10
    assert effects[1]["name"] == "Haste"
    assert effects[1]["duration"] == 5
    
    # Test updating effects
    manager.update_spell_effects(mock_game_state, 3)
    effects = mock_game_state.current_state["player"]["Spell Effects"]
    assert len(effects) == 2
    assert effects[0]["duration"] == 7
    assert effects[1]["duration"] == 2
    
    # Test effect expiration
    manager.update_spell_effects(mock_game_state, 10)
    effects = mock_game_state.current_state["player"]["Spell Effects"]
    assert len(effects) == 0

def test_spell_effects_invalid(mock_game_state: MagicMock) -> None:
    """Test spell effect management with invalid input."""
    manager = CharacterManager(MagicMock())
    
    with pytest.raises(ValueError, match="Spell effect name must be a string"):
        manager.add_spell_effect(mock_game_state, cast(str, 123), 10)
    
    with pytest.raises(ValueError, match="Duration must be a non-negative integer"):
        manager.add_spell_effect(mock_game_state, "Bless", -1)
    
    with pytest.raises(ValueError, match="Rounds must be a non-negative integer"):
        manager.update_spell_effects(mock_game_state, -1) 