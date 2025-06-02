from dataclasses import dataclass
from typing import Optional
import os

@dataclass
class AzureConfig:
    """Azure-specific configuration."""
    endpoint: str
    key_vault_name: str = "aoaikeys"
    secret_name: str = "AOAIKey"
    model: str = "gpt-4o-mini"

@dataclass
class AnthropicConfig:
    """Anthropic-specific configuration."""
    model: str = "claude-3-opus-20240229"
    api_key: Optional[str] = None

@dataclass
class GameConfig:
    """Game-specific configuration."""
    debug_mode: bool = False
    self_play: bool = False
    save_file: Optional[str] = None
    player_file: Optional[str] = None
    scenario_file: Optional[str] = None

@dataclass
class Config:
    """Main configuration class."""
    azure: Optional[AzureConfig] = None
    anthropic: Optional[AnthropicConfig] = None
    game: GameConfig = GameConfig()

    @classmethod
    def from_env(cls) -> 'Config':
        """Create a configuration from environment variables."""
        azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        azure_config = None
        if azure_endpoint:
            azure_config = AzureConfig(
                endpoint=azure_endpoint,
                key_vault_name=os.getenv("AZURE_KEY_VAULT_NAME", "aoaikeys"),
                secret_name=os.getenv("AZURE_SECRET_NAME", "AOAIKey"),
                model=os.getenv("AZURE_MODEL", "gpt-4o-mini")
            )

        anthropic_config = None
        if os.getenv("ANTHROPIC_API_KEY"):
            anthropic_config = AnthropicConfig(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
            )

        game_config = GameConfig(
            debug_mode=os.getenv("GAME_DEBUG", "").lower() in ("true", "1", "yes"),
            self_play=os.getenv("GAME_SELF_PLAY", "").lower() in ("true", "1", "yes"),
            save_file=os.getenv("GAME_SAVE_FILE"),
            player_file=os.getenv("GAME_PLAYER_FILE"),
            scenario_file=os.getenv("GAME_SCENARIO_FILE")
        )

        return cls(
            azure=azure_config,
            anthropic=anthropic_config,
            game=game_config
        ) 