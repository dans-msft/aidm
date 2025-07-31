"""Action resolution module."""

import json
import logging
import random
from typing import Any, Dict, List, Optional, Tuple, Union
import d20

from ..schemas import round_schema, response_schema, game_state_schema, response_and_state_schema
from ..prompts import ACTION_RULES, GAME_RULES, RESPONSE_RULES, STATE_CHANGE_RULES, RESPONSE_AND_STATE_CHANGE_RULES, DEATH_RULES
from adventure.llm.client import LLMClient
from adventure.core.game_state import GameState
from adventure.core.location import LocationManager
from adventure.core.state_validator import StateValidator

class ActionResolver:
    """Resolves player commands into game actions."""
    
    def __init__(self, llm_client: LLMClient, location_manager: Optional[LocationManager] = None) -> None:
        """Initialize the action resolver.
        
        Args:
            llm_client: The LLM client to use for action resolution.
            location_manager: Optional location manager for world context.
        """
        self.llm_client = llm_client
        self.location_manager = location_manager
        self.state_validator = StateValidator()
    
    @property
    def client(self) -> LLMClient:
        """Get the LLM client instance."""
        return self.llm_client

    def _get_world_context(self, game_state: Dict[str, Any], context_type: str = "action") -> str:
        """Get formatted world context for the current location.
        
        Args:
            game_state: The current game state.
            context_type: Type of context needed ('action', 'narrative', 'exploration', 'dm').
            
        Returns:
            Formatted world context string.
        """
        if not self.location_manager or 'location' not in game_state:
            logging.debug("No location found in game state")
            return ""
        
        current_location = game_state['location']
        logging.debug(f"Game state location: {current_location}")
        
        if context_type == "action":
            context = self.location_manager.get_action_context(current_location)
            return self.location_manager.format_context_for_prompt(context, include_dm_notes=False)
        elif context_type == "narrative":
            context = self.location_manager.get_narrative_context(current_location)
            return self.location_manager.format_context_for_prompt(context, include_dm_notes=False)
        elif context_type == "exploration":
            context = self.location_manager.get_exploration_context(current_location)
            return self.location_manager.format_context_for_prompt(context, include_dm_notes=False)
        elif context_type == "dm":
            context = self.location_manager.get_dm_context(current_location)
            return self.location_manager.format_context_for_prompt(context, include_dm_notes=True)
        else:
            context = self.location_manager.get_action_context(current_location)
            return self.location_manager.format_context_for_prompt(context, include_dm_notes=False)

    async def turn(self, command: str, game_state: Dict[str, Any], context: List[Tuple[str, str]], debug: bool = False) -> str:
        """Process a single turn of the game.
        
        Args:
            command: The player's command
            game_state: The current game state
            context: The conversation context
            debug: Whether debug mode is enabled
            
        Returns:
            The response to show to the player
        """
        # Handle game commands directly
        '''
        if command.lower() in ["save", "load", "quit", "debug"]:
            if command == "save":
                return "Game saved."
            elif command == "load":
                return "Use --load-game to load a saved game."
            elif command == "quit":
                return "Game ended."
            elif command == "debug":
                return f"Debug mode {'enabled' if debug else 'disabled'}."
        '''
        
        # Get action resolution from LLM
        world_context = self._get_world_context(game_state, "dm")
        system_prompt = f"{ACTION_RULES}\nGame State: {json.dumps(game_state, indent=4)}"
        if world_context:
            system_prompt += f"\n\n{world_context}"
        max_retries = 3
        retry_count = 0

        if debug:
            print(system_prompt)
        
        while retry_count < max_retries:
            result = await self.llm_client.make_structured_request(
                prompt=command,
                context=context,
                system_prompt=system_prompt,
                schema=round_schema,
                name="get_actions"
            )
            if debug:
                print(json.dumps(result, indent=2))

            if 'actions' in result and isinstance(result['actions'], list):
                break
                
            retry_count += 1
            if retry_count == max_retries:
                logging.error(f"Failed to get valid actions list after {max_retries} attempts")
                return "I'm having trouble processing that action. Please try again."
            logging.warning(f"Invalid actions format, retrying ({retry_count}/{max_retries})")

        actions = result['actions']
        
        # Process each action
        success_message = ""
        for action in actions:
            # Handle game commands from LLM
            '''
            if action['action_type'] in ['debug_mode_on', 'debug_mode_off', 'save_game', 'quit_game']:
                if action['action_type'] == 'debug_mode_on':
                    return "Debug mode enabled."
                if action['action_type'] == 'debug_mode_off':
                    return "Debug mode disabled."
                if action['action_type'] == 'save_game':
                    return "Game saved."
                if action['action_type'] == 'quit_game':
                    return "Game ended."
            '''

            # Handle movement requests
            ok_to_roll = True
            current_location = game_state['location']
            if action['how_to_resolve'] == 'check_map':
                if self.location_manager and not self.location_manager.can_move_to(current_location, action['target']):
                    success_message += action['result_if_failed'] + '\n'
                    ok_to_roll = False
            
            # Handle dice rolls
            if action['dice_to_roll'] and ok_to_roll:
                try:
                    roll = self._roll_dice(action['dice_to_roll'], action['advantage'], action['disadvantage'])
                    if roll >= action['number_to_beat']:
                        success_message += action['result_if_successful'] + "\n"
                    else:
                        success_message += action['result_if_failed'] + "\n"
                except d20.errors.RollSyntaxError as e:
                    logging.error(f'Die roll error: {e}')
            else:
                success_message += action['result_if_successful'] + "\n"

        if debug:
            print(f'Success message: {success_message}')
        
        # Get responses from LLM
        world_context = self._get_world_context(game_state, "narrative")
        system_prompt = f"{GAME_RULES}\n{RESPONSE_RULES}\nGame State: {json.dumps(game_state, indent=4)}\nAction Result: {success_message}"
        if world_context:
            system_prompt += f"\n\n{world_context}"
        response = await self.llm_client.make_structured_request(
            prompt=command,
            context=context,
            system_prompt=system_prompt,
            schema=response_schema,
            name='get_response',
            use_detailed_model=True
        )
        if debug:
            print(json.dumps(response, indent=2))
        
        # Update game state based on responses with validation and retry
        world_context = self._get_world_context(game_state, "dm")
        base_system_prompt = f"{GAME_RULES}\n{STATE_CHANGE_RULES}\nPrior State: {json.dumps(game_state, indent=4)}\n{response['DM_response']}"
        if world_context:
            base_system_prompt += f"\n\n{world_context}"
        
        # Try to get a valid state update with retries
        max_state_retries = 2
        new_game_state = None
        validation_feedback = ""
        
        for attempt in range(max_state_retries + 1):
            system_prompt = base_system_prompt + validation_feedback
            
            candidate_state = await self.llm_client.make_structured_request(
                prompt="update game state",
                system_prompt=system_prompt,
                schema=game_state_schema,
                name='update_state',
                max_tokens=10000
            )
            
            if debug:
                print(f"State update attempt {attempt + 1}:")
                print(json.dumps(candidate_state, indent=2))
            
            # Validate the proposed state changes
            validation_result = self.state_validator.validate_state_changes(
                game_state, candidate_state, success_message
            )
            
            if validation_result.is_valid or attempt == max_state_retries:
                # Either validation passed or we're out of retries
                if validation_result.is_valid:
                    new_game_state = candidate_state
                    if debug:
                        print("State validation passed")
                else:
                    # Use defensive merging as fallback
                    if debug:
                        print(f"State validation failed after {max_state_retries + 1} attempts, using defensive merge")
                        print(f"Validation issues: {validation_result.issues}")
                    new_game_state = self.state_validator.merge_states_defensively(game_state, candidate_state)
                break
            else:
                # Validation failed, prepare feedback for retry
                if debug:
                    print(f"State validation failed on attempt {attempt + 1}: {validation_result.issues}")
                validation_feedback = f"\n\nVALIDATION ERRORS FROM PREVIOUS ATTEMPT:\n{chr(10).join(validation_result.issues)}\nPlease fix these issues and preserve unchanged fields exactly."

        '''
        system_prompt = f"{GAME_RULES}\n{RESPONSE_AND_STATE_CHANGE_RULES}\nGame State: {json.dumps(game_state, indent=4)}\nAction Result: {success_message}"
        response = self.llm_client.make_structured_request(
            prompt=command,
            context=context,
            system_prompt=system_prompt,
            schema=response_and_state_schema
        )
        if debug:
            print(json.dumps(response, indent=2))
        new_game_state = response['new_state']
        '''
        
        # Check for player death
        if 'player' in new_game_state and 'HP' in new_game_state['player'] and new_game_state['player']['HP'] <= 0:
            print("Detected death")
            prompt = f"Game State: {json.dumps(new_game_state, indent=4)}"
            death_response = await self.llm_client.make_structured_request(
                prompt=prompt,
                system_prompt=DEATH_RULES,
                schema=response_schema
            )
            return death_response['player_response']
        
        # Update context and game state
        context.append((command, response['player_response']))
        game_state.update(new_game_state)
        
        return response['player_response']
    
    def _roll_dice(self, dice_to_roll: str, advantage: bool = False, disadvantage: bool = False) -> int:
        """Roll dice using a dice expression with optional advantage or disadvantage.
        
        Args:
            dice_to_roll: The dice expression to roll (e.g., "3d6+5").
            advantage: Whether to roll with advantage.
            disadvantage: Whether to roll with disadvantage.
            
        Returns:
            The result of the roll.
            
        Raises:
            d20.errors.RollSyntaxError: If the dice expression is invalid.
        """
        result = d20.roll(dice_to_roll).total
        if advantage:
            result2 = d20.roll(dice_to_roll).total
            if result2 > result:
                result = result2
        if disadvantage:
            result2 = d20.roll(dice_to_roll).total
            if result2 < result:
                result = result2
        return result 