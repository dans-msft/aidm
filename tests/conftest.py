"""Pytest configuration and fixtures."""

import json
import pytest
from pathlib import Path
from typing import Dict, Generator
from unittest.mock import MagicMock

from adventure.core import GameState, ActionResolver, CharacterManager
from adventure.llm.client import LLMClient
from adventure.log_config import setup_logging

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"

@pytest.fixture
def test_logger() -> Generator:
    """Create a test logger that logs to a temporary file."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        logger = setup_logging(f.name, debug=True)
        yield logger
        # Clean up log file after test
        Path(f.name).unlink()

@pytest.fixture(scope="session")
def mock_llm_client() -> Generator[MagicMock, None, None]:
    """Create a mock LLM client for testing."""
    client = MagicMock(spec=LLMClient)
    client.make_structured_request = MagicMock()
    yield client

@pytest.fixture(scope="session")
def mock_game_state() -> Generator[MagicMock, None, None]:
    """Create a mock game state for testing."""
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
    yield state

@pytest.fixture
def test_game_state() -> GameState:
    """Create a test game state."""
    return GameState({
        "player": {
            "Name": "Test Player",
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
        },
        "location": "Test Location",
        "danger": "safe",
        "time_of_day": "12:00",
        "sunrise": "06:00",
        "sunset": "18:00",
        "date": "July 1",
        "dark": False,
        "monsters": [],
        "NPCs": []
    })

@pytest.fixture
def test_action_resolver(mock_llm_client: LLMClient) -> ActionResolver:
    """Create a test action resolver."""
    return ActionResolver(mock_llm_client)

@pytest.fixture
def test_character_manager(mock_llm_client: LLMClient) -> CharacterManager:
    """Create a test character manager."""
    return CharacterManager(mock_llm_client)

@pytest.fixture
def test_player_file(tmp_path: Path) -> Path:
    """Create a test player file."""
    player_file = tmp_path / "test_player.txt"
    player_file.write_text("""
    A human fighter named Test Player. They are a skilled warrior with a focus on strength and constitution.
    They carry a longsword and are proficient in athletics. They have no magical abilities.
    """)
    return player_file

@pytest.fixture
def test_scenario_file(tmp_path: Path) -> Path:
    """Create a test scenario file."""
    scenario_file = tmp_path / "test_scenario.txt"
    scenario_file.write_text("""
    You find yourself in a small village on the edge of a dark forest. The village is peaceful and safe,
    with a few shops and a tavern. The forest to the north is known to be dangerous, with rumors of
    goblins and other creatures.
    """)
    return scenario_file

@pytest.fixture
def test_save_file(tmp_path: Path, test_game_state: GameState) -> Path:
    """Create a test save file."""
    save_file = tmp_path / "test_save.sav"
    test_game_state.save(str(save_file))
    return save_file 