"""Main entry point for the adventure game."""

import argparse
import asyncio
import logging
import sys
import datetime
import json
from typing import Any, Dict
from pathlib import Path

from .llm.client import LLMClient
from .prompts import WORLD_MAP_RULES
from .log_config import setup_logging, get_logger

DEFAULT_LOG_DIR = "logs"

def parse_args() -> argparse.Namespace:
    """Parse command line arguments.
    
    Returns:
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description="Fantasy RPG Adventure Game")
    
    # Game setup arguments
    parser.add_argument('--scenario', type=str, required=False,
                       help='Path to the scenario file describing the game world')
    parser.add_argument('--api-key', type=str, required=True,
                       help='API Key for the LLM provider')
    parser.add_argument('--provider', type=str, choices=['openai', 'anthropic'], default='anthropic',
                       help='LLM provider to use (openai or anthropic)')
    parser.add_argument('--out', type=str, default='world.json',
                        help='Name of output file for world data')
    
    # Game options
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    parser.add_argument('--log-file', type=str, required=False,
                       help='Path to log file (default: logs/adventure.log)')
    
    args = parser.parse_args()
    
    # Set default log file if not specified
    if not args.log_file:
        log_dir = Path(DEFAULT_LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)
        args.log_file = str(log_dir / "adventure.log")
    
    return args

async def create_world(args: argparse.Namespace) -> Dict[str, Any]:
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
        endpoint='none',
        api_key=args.api_key,
        provider=args.provider
    )
    
    # Initialize game components
    logger.debug("Creating game components...")
    from adventure.schemas import game_map_schema

    with open(args.scenario, 'r') as f:
        scenario_description = f.read()
        
    # Make LLM call to generate the world map
    system_prompt = WORLD_MAP_RULES
    
    world_map = await llm_client.make_structured_request(
        prompt=scenario_description,
        system_prompt=system_prompt,
        schema=game_map_schema,
        name='generate_map',
        max_tokens = 20000
    )
        
    print(json.dumps(world_map, indent=2))
    return world_map

async def main() -> None:
    """Main entry point."""
    # Parse arguments
    args = parse_args()
    
    # Set up logging
    logger = setup_logging(args.log_file, args.debug)
    world_map = await create_world(args)
    
    # Write world map to output file
    logger.info(f"Writing world map to {args.out}")
    with open(args.out, 'w') as f:
        json.dump(world_map, f, indent=2)
    logger.info("World map written successfully")

if __name__ == "__main__":
    asyncio.run(main()) 