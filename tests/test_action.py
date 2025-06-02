"""Tests for the ActionResolver class."""

import pytest
from unittest.mock import Mock, patch

from adventure.core import ActionResolver, GameState
from adventure.llm.client import LLMClient

def test_action_resolver_initialization(mock_llm_client: LLMClient):
    """Test that action resolver initializes correctly."""
    resolver = ActionResolver(mock_llm_client)
    assert resolver.llm_client == mock_llm_client

@pytest.mark.asyncio
async def test_resolve_actions(mock_llm_client: LLMClient, test_game_state: GameState):
    """Test resolving player actions."""
    resolver = ActionResolver(mock_llm_client)
    
    # Mock LLM response for a simple action
    mock_response = {
        "success": True,
        "message": "You move to the forest.",
        "actions": {
            "location": "Forest",
            "danger": "moderate"
        }
    }
    mock_llm_client.make_structured_request.return_value = mock_response
    
    # Test resolving a simple action
    success_message, actions = await resolver.resolve_actions(
        "I go to the forest",
        test_game_state
    )
    
    assert success_message == "You move to the forest."
    assert actions == {"location": "Forest", "danger": "moderate"}
    
    # Test resolving a game command
    success_message, actions = await resolver.resolve_actions(
        "save",
        test_game_state
    )
    
    assert success_message is None
    assert actions == {"command": "save"}

@pytest.mark.asyncio
async def test_get_response(mock_llm_client: LLMClient, test_game_state: GameState):
    """Test getting game responses."""
    resolver = ActionResolver(mock_llm_client)
    
    # Mock LLM response for a simple action
    mock_response = {
        "response": "You enter a dark forest. The trees loom overhead, and you hear strange noises in the distance."
    }
    mock_llm_client.make_structured_request.return_value = mock_response
    
    # Test getting response for a successful action
    response = await resolver.get_response(
        "You move to the forest.",
        test_game_state
    )
    
    assert response == "You enter a dark forest. The trees loom overhead, and you hear strange noises in the distance."
    
    # Test getting response for a game command
    response = await resolver.get_response(
        None,
        test_game_state,
        command="save"
    )
    
    assert response == "Game saved."

@pytest.mark.asyncio
async def test_update_game_state(mock_llm_client: LLMClient, test_game_state: GameState):
    """Test updating game state from DM response."""
    resolver = ActionResolver(mock_llm_client)
    
    # Mock LLM response for state update
    mock_response = {
        "state_updates": {
            "location": "Forest",
            "danger": "moderate",
            "dark": True,
            "monsters": ["Goblin"]
        }
    }
    mock_llm_client.make_structured_request.return_value = mock_response
    
    # Test updating state
    await resolver.update_game_state(
        "You enter a dark forest...",
        test_game_state
    )
    
    assert test_game_state.current_state["location"] == "Forest"
    assert test_game_state.current_state["danger"] == "moderate"
    assert test_game_state.current_state["dark"]
    assert test_game_state.current_state["monsters"] == ["Goblin"]

def test_roll_dice():
    """Test dice rolling functionality."""
    resolver = ActionResolver(Mock())
    
    # Test normal roll
    roll = resolver._roll_dice(20)
    assert 1 <= roll <= 20
    
    # Test roll with advantage
    roll = resolver._roll_dice(20, advantage=True)
    assert 1 <= roll <= 20
    
    # Test roll with disadvantage
    roll = resolver._roll_dice(20, disadvantage=True)
    assert 1 <= roll <= 20
    
    # Test invalid dice size
    with pytest.raises(ValueError):
        resolver._roll_dice(0)
    
    with pytest.raises(ValueError):
        resolver._roll_dice(-1)

@pytest.mark.asyncio
async def test_action_resolver_error_handling(mock_llm_client: LLMClient, test_game_state: GameState):
    """Test error handling in action resolver."""
    resolver = ActionResolver(mock_llm_client)
    
    # Test LLM client error
    mock_llm_client.make_structured_request.side_effect = Exception("LLM error")
    
    with pytest.raises(Exception) as exc_info:
        await resolver.resolve_actions("test command", test_game_state)
    assert str(exc_info.value) == "LLM error"
    
    # Test invalid action response
    mock_llm_client.make_structured_request.return_value = {"invalid": "response"}
    
    with pytest.raises(ValueError) as exc_info:
        await resolver.resolve_actions("test command", test_game_state)
    assert "Invalid action response" in str(exc_info.value)
    
    # Test invalid state update response
    mock_llm_client.make_structured_request.return_value = {"invalid": "response"}
    
    with pytest.raises(ValueError) as exc_info:
        await resolver.update_game_state("test response", test_game_state)
    assert "Invalid state update response" in str(exc_info.value) 