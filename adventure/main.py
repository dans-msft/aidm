"""Main entry point for the adventure game."""

import argparse
import asyncio
import logging
import sys
import datetime
import json
from typing import Optional, Tuple
from pathlib import Path

from .core import GameState, ActionResolver, CharacterManager, LocationManager
from .llm.client import LLMClient
from .prompts import SELF_PLAY_PROMPT
from .log_config import setup_logging, get_logger

# Default configuration
DEFAULT_ENDPOINT = "https://dasommer-oai-cmk.openai.azure.com/openai/deployments/gpt-4o/chat/completions?api-version=2024-09-01-preview"
DEFAULT_LOG_DIR = "logs"

def generate_save_filename(character_name: str) -> str:
    """Generate a save filename based on character name and timestamp.
    
    Args:
        character_name: The name of the character
        
    Returns:
        A filename string in the format character_name_YYYYMMDD_HHMMSS.sav
    """
    # Convert the character name to lowercase and replace spaces with underscores
    formatted_name = character_name.lower().replace(" ", "_")
    
    # Get the current date and time
    now = datetime.datetime.now()
    
    # Format the date and time as YYYYMMDD_HHMMSS
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    
    # Combine the formatted name and timestamp
    return f"{formatted_name}_{timestamp}.sav"

def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description="Fantasy RPG Adventure Game")
    
    # Game setup arguments
    parser.add_argument('--scenario', type=str, required=False,
                       help='Path to the scenario file describing the game world')
    parser.add_argument('--player', type=str, required=False,
                       help='Path to the player file describing character attributes')
    parser.add_argument('--world-map', type=str, default='world.json',
                       help='Path to the world map JSON file (default: world.json)')
    parser.add_argument('--load-game', type=str, required=False,
                       help='Path to a saved game file to load')
    
    # LLM configuration
    parser.add_argument('--endpoint', type=str, default=DEFAULT_ENDPOINT,
                       help='URI to OAI or AOAI endpoint')
    parser.add_argument('--api-key', type=str, required=True,
                       help='API Key for the LLM provider')
    parser.add_argument('--provider', type=str, choices=['openai', 'anthropic'], default='anthropic',
                       help='LLM provider to use (openai or anthropic)')
    
    # Game options
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    parser.add_argument('--self-play', action='store_true',
                       help='Enable self-play mode')
    parser.add_argument('--log-file', type=str, required=False,
                       help='Path to log file (default: logs/adventure.log)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.load_game and (not args.player or not args.scenario):
        parser.error("--player and --scenario are required if --load-game is not specified")
    
    # Set default log file if not specified
    if not args.log_file:
        log_dir = Path(DEFAULT_LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)
        args.log_file = str(log_dir / "adventure.log")
    
    return args

async def initialize_game(args: argparse.Namespace) -> Tuple[GameState, ActionResolver, CharacterManager]:
    """Initialize the game components.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        Tuple of (game_state, action_resolver, character_manager)
        
    Raises:
        ValueError: If game initialization fails
    """
    logger = get_logger()
    logger.info("Initializing game components...")
    
    # Initialize LLM client
    logger.debug("Creating LLM client...")
    llm_client = LLMClient(
        endpoint=args.endpoint,
        api_key=args.api_key,
        provider=args.provider
    )
    
    # Initialize location manager
    logger.debug("Loading world map...")
    location_manager = None
    if Path(args.world_map).exists():
        try:
            location_manager = LocationManager(world_file=args.world_map)
            logger.info(f"Loaded world map from {args.world_map}")
        except Exception as e:
            logger.warning(f"Failed to load world map from {args.world_map}: {e}")
            logger.info("Continuing without world map")
    else:
        logger.warning(f"World map file {args.world_map} not found, continuing without world map")
    
    # Initialize game components
    logger.debug("Creating game components...")
    action_resolver = ActionResolver(llm_client, location_manager)
    character_manager = CharacterManager(llm_client)
    
    # Load or create game state
    game_state = GameState()
    if args.load_game:
        logger.info(f"Loading game from {args.load_game}...")
        loaded_state = game_state.load(args.load_game)
        if loaded_state is None:
            raise ValueError(f"Failed to load game from {args.load_game}")
        game_state = loaded_state
    else:
        logger.info("Creating new game...")
        # Create character from player file
        logger.debug(f"Reading player file: {args.player}")
        with open(args.player, 'r') as f:
            player_description = f.read()
        character = await character_manager.create_character(player_description)
        
        # Create initial game state from scenario
        logger.debug(f"Reading scenario file: {args.scenario}")
        with open(args.scenario, 'r') as f:
            scenario_description = f.read()
        
        # Initialize game state using LLM
        logger.debug("Initializing game state from scenario and player descriptions...")
        from adventure.prompts import STATE_CHANGE_RULES
        from adventure.schemas import game_state_schema
        
        # Make LLM call to determine initial game state
        system_prompt = STATE_CHANGE_RULES + '\n' + json.dumps(character, indent=4) + '\n' + \
            scenario_description + '\n' + player_description
        
        # Add world overview if location manager is available
        if location_manager:
            world_overview = location_manager.get_world_overview()
            system_prompt += f'\n\n{world_overview}'
        
        initial_state = await llm_client.make_structured_request(
            prompt=player_description,
            system_prompt=system_prompt,
            schema=game_state_schema,
            name='initial_state'
        )
        
        game_state = GameState(initial_state)
        
        # Add context
        game_state.add_to_context('Game World', scenario_description)
        game_state.add_to_context('Player', player_description)
        
        # Initialize game with first turn
        logger.debug("Starting first turn...")
        if args.debug:
            print("Initial state:")
            print(json.dumps(initial_state, indent=2))
        response = await action_resolver.turn(
            "begin the game",
            game_state.current_state,
            game_state.context,
            args.debug
        )
    
    logger.info("Game initialization complete")
    return game_state, action_resolver, character_manager

async def game_loop(game_state: GameState, action_resolver: ActionResolver,
             character_manager: CharacterManager, args: argparse.Namespace) -> None:
    """Run the main game loop.
    
    Args:
        game_state: The game state manager
        action_resolver: The action resolver
        character_manager: The character manager
        args: Parsed command line arguments
    """
    logger = get_logger()
    logger.info("Starting game loop...")
    
    # Initialize self-play if enabled
    self_play_context: list[tuple[str, str]] = []
    llm_client = action_resolver.client
    
    if args.self_play:
        logger.info("Self-play mode enabled")
    
    # Get initial response
    if args.load_game:
        last_response = game_state.context[-1][1] if game_state.context else "Welcome back!"
        logger.info("Resuming saved game")
    else:
        last_response = game_state.context[-1][1]
        logger.info("New game started")
    
    print(last_response)
    
    # Main game loop
    while True:
        try:
            # Get command
            if args.self_play:
                logger.debug("Generating self-play command...")
                command = await llm_client.make_self_play_request(
                    SELF_PLAY_PROMPT,
                    last_response,
                    self_play_context or []
                )
                self_play_context.append((last_response, command))
                print(f'> {command}')
            else:
                command = input('> ')
            
            logger.debug(f"Processing command: {command}")
            
            # Process command using the new turn function
            response = await action_resolver.turn(
                command,
                game_state.current_state,
                game_state.context,
                args.debug
            )
            
            # Handle special responses
            if response == "Game saved.":
                filename = game_state.save(generate_save_filename(game_state.current_state["player"]["Name"]))
                logger.info(f"Game saved to {filename}")
                print(f'Game saved to {filename}')
                continue
            elif response == "Game ended.":
                filename = game_state.save(generate_save_filename(game_state.current_state["player"]["Name"]))
                logger.info(f"Game saved to {filename} before quit")
                print(f'Game saved to {filename}')
                print('Thank you for playing!')
                sys.exit(0)
            elif response.startswith("Debug mode"):
                if "enabled" in response:
                    args.debug = True
                    logger.setLevel(logging.DEBUG)
                else:
                    args.debug = False
                    logger.setLevel(logging.INFO)
                print(response)
                continue
            
            # Print response and update last response
            print(response)
            last_response = response
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, saving game...")
            print("\nSaving game before exit...")
            filename = game_state.save(generate_save_filename(game_state.current_state["player"]["Name"]))
            logger.info(f"Game saved to {filename}")
            print(f'Game saved to {filename}')
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error during game loop: {e}", exc_info=args.debug)
            if args.debug:
                raise
            print(f"\nAn error occurred: {e}")
            print("The game will attempt to continue...")

async def main() -> None:
    """Main entry point."""
    # Parse arguments
    args = parse_args()
    
    # Set up logging
    logger = setup_logging(args.log_file, args.debug)
    logger.info("Starting adventure game...")
    
    try:
        # Initialize game
        game_state, action_resolver, character_manager = await initialize_game(args)
        logger.debug(f"Game state: {json.dumps(game_state.current_state, indent=4)}")
        
        # Run game loop
        await game_loop(game_state, action_resolver, character_manager, args)
    except Exception as e:
        logger.error("Fatal error:", exc_info=True)
        print(f"\nFatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 