# Adventure Game

A fantasy role-playing game powered by Large Language Models (LLMs). This game combines traditional RPG mechanics with AI-driven storytelling and character interaction.

## Features

- AI-powered character creation and interaction
- Dynamic storytelling and world-building
- Traditional RPG mechanics (combat, skills, spells)
- Save/load game state
- Self-play mode for AI-driven gameplay

## Installation

1. Clone the repository:
```bash
git clone https://github.com/dansommerfield/adventure.git
cd adventure
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package in development mode with all dependencies:
```bash
pip install -e ".[dev]"
```

4. Configure Azure Key Vault:
   - Create an Azure Key Vault
   - Add your LLM API key as a secret
   - Set up authentication (see [Azure Identity documentation](https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme))

## Usage

Start a new game:
```bash
python -m adventure.main --player player.txt --scenario scenario.txt
```

Load a saved game:
```bash
python -m adventure.main --load-game character_name_20240321_123456.sav
```

Enable debug mode:
```bash
python -m adventure.main --player player.txt --scenario scenario.txt --debug
```

Enable self-play mode:
```bash
python -m adventure.main --player player.txt --scenario scenario.txt --self-play
```

Use a different LLM endpoint:
```bash
python -m adventure.main --player player.txt --scenario scenario.txt --endpoint "https://your-endpoint"
```

## Development

### Running Tests

Run the test suite:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=adventure --cov-report=term-missing
```

### Code Quality

Format code:
```bash
black .
isort .
```

Type checking:
```bash
mypy .
```

Linting:
```bash
ruff check .
```

### Project Structure

```
adventure/
├── adventure/
│   ├── core/           # Core game logic
│   │   ├── __init__.py
│   │   ├── action.py   # Action resolution
│   │   ├── character.py # Character management
│   │   └── game_state.py # Game state management
│   ├── llm/            # LLM client
│   │   ├── __init__.py
│   │   └── client.py   # LLM client implementation
│   ├── __init__.py
│   ├── logging.py      # Logging configuration
│   └── main.py         # Main entry point
├── tests/              # Test suite
│   ├── __init__.py
│   ├── conftest.py     # Test configuration
│   └── test_*.py       # Test modules
├── pyproject.toml      # Project configuration
└── README.md           # This file
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
