"""Tests for the GameState class."""

import json
from pathlib import Path
import pytest

from adventure.core import GameState

def test_game_state_initialization(test_game_state: GameState):
    """Test that game state initializes correctly."""
    assert test_game_state.current_state["player"]["Name"] == "Test Player"
    assert test_game_state.current_state["location"] == "Test Location"
    assert test_game_state.current_state["danger"] == "safe"
    assert not test_game_state.current_state["dark"]

def test_game_state_update(test_game_state: GameState):
    """Test updating game state."""
    updates = {
        "location": "Forest",
        "danger": "moderate",
        "dark": True,
        "monsters": ["Goblin"]
    }
    test_game_state.update(updates)
    
    assert test_game_state.current_state["location"] == "Forest"
    assert test_game_state.current_state["danger"] == "moderate"
    assert test_game_state.current_state["dark"]
    assert test_game_state.current_state["monsters"] == ["Goblin"]

def test_game_state_context(test_game_state: GameState):
    """Test adding and clearing context."""
    test_game_state.add_to_context("player", "I look around the room.")
    test_game_state.add_to_context("dm", "You see a table and a chair.")
    
    assert len(test_game_state.context) == 2
    assert test_game_state.context[0] == ("player", "I look around the room.")
    assert test_game_state.context[1] == ("dm", "You see a table and a chair.")
    
    test_game_state.clear_context()
    assert len(test_game_state.context) == 0

def test_game_state_save_load(tmp_path: Path, test_game_state: GameState):
    """Test saving and loading game state."""
    save_file = tmp_path / "test_save.sav"
    test_game_state.save(str(save_file))
    
    # Create new game state and load from file
    loaded_state = GameState()
    loaded_state.load(str(save_file))
    
    assert loaded_state.current_state == test_game_state.current_state
    assert loaded_state.context == test_game_state.context

def test_game_state_checks(test_game_state: GameState):
    """Test various game state checks."""
    # Test player status checks
    assert not test_game_state.is_player_dead()
    assert test_game_state.get_player_status() == "Normal"
    
    # Test location checks
    assert not test_game_state.is_dark()
    assert test_game_state.get_danger_level() == "safe"
    assert test_game_state.get_location() == "Test Location"
    
    # Test time checks
    assert test_game_state.get_time_of_day() == "12:00"
    assert test_game_state.get_date() == "July 1"
    
    # Test monster and NPC checks
    assert not test_game_state.has_monsters()
    assert not test_game_state.has_npcs()
    
    # Update state and test again
    test_game_state.update({
        "player": {"Status": "Unconscious", "HP": 0},
        "dark": True,
        "danger": "high",
        "monsters": ["Goblin"],
        "NPCs": ["Villager"]
    })
    
    assert test_game_state.is_player_dead()
    assert test_game_state.get_player_status() == "Unconscious"
    assert test_game_state.is_dark()
    assert test_game_state.get_danger_level() == "high"
    assert test_game_state.has_monsters()
    assert test_game_state.has_npcs()

def test_game_state_invalid_updates(test_game_state: GameState):
    """Test handling of invalid state updates."""
    # Test with invalid player data
    with pytest.raises(ValueError):
        test_game_state.update({"player": "invalid"})
    
    # Test with invalid location
    with pytest.raises(ValueError):
        test_game_state.update({"location": 123})
    
    # Test with invalid danger level
    with pytest.raises(ValueError):
        test_game_state.update({"danger": "invalid"})

def test_game_state_file_operations(tmp_path: Path, test_game_state: GameState):
    """Test file operations with invalid paths and permissions."""
    # Test with non-existent directory
    with pytest.raises(FileNotFoundError):
        test_game_state.save(str(tmp_path / "nonexistent" / "save.sav"))
    
    # Test with invalid file path
    with pytest.raises(OSError):
        test_game_state.save("/invalid/path/save.sav")
    
    # Test loading non-existent file
    with pytest.raises(FileNotFoundError):
        test_game_state.load(str(tmp_path / "nonexistent.sav"))
    
    # Test loading invalid save file
    invalid_file = tmp_path / "invalid.sav"
    invalid_file.write_text("invalid json")
    with pytest.raises(json.JSONDecodeError):
        test_game_state.load(str(invalid_file)) 