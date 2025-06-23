"""Character-related JSON schemas for the game."""

# Ability scores schema
ability_schema = {
    "type": "object",
    "properties": {
        "Strength": {"type": "integer"},
        "Dexterity": {"type": "integer"},
        "Constitution": {"type": "integer"},
        "Intelligence": {"type": "integer"},
        "Wisdom": {"type": "integer"},
        "Charisma": {"type": "integer"}
    },
    "required": ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"],
    "additionalProperties": False
}

# Spell slots schema
spell_slots_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "level": {"type": "integer"},
            "slots": {"type": "integer"},
            "max_slots": {"type": "integer"}
        },
        "required": ["level", "slots", "max_slots"],
        "additionalProperties": False
    }
}

# Magic schema
magic_schema = {
    "type": "object",
    "properties": {
        "Spells_Known": {
            "type": "array",
            "items": {"type": "string"}
        },
        "Cantrips_Known": {
            "type": "array",
            "items": {"type": "string"}
        },
        "Spell_Slots": spell_slots_schema
    },
    "required": ["Spells_Known", "Cantrips_Known", "Spell_Slots"],
    "additionalProperties": False
}

# Spell effects schema
spell_effects_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "effect": {"type": "string"},
            "minutes_remaining": {"type": "integer"}
        },
        "required": ["effect", "minutes_remaining"],
        "additionalProperties": False
    }
}

# Character schema
character_schema = {
    "type": "object",
    "properties": {
        "Name": {"type": "string"},
        "Pronouns": {"type": "string"},
        "Race": {"type": "string"},
        "Class": {"type": "string"},
        "Level": {"type": "integer"},
        "XP": {"type": "integer"},
        "HP": {"type": "integer"},
        "Max_HP": {"type": "integer"},
        "Status": {"type": "string"},
        "Gold": {"type": "integer"},
        "AC": {"type": "integer"},
        "Abilities": ability_schema,
        "Proficiencies": {
            "type": "object",
            "properties": {
                "Skills": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "Weapons": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "Saving_Throws": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["Skills", "Weapons", "Saving_Throws"],
            "additionalProperties": False
        },
        "Magic": magic_schema,
        "Spell_Effects": spell_effects_schema,
        "Inventory": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": [
        "Name", "Pronouns", "Race", "Class", "Level", "XP", "HP", "Max_HP",
        "Status", "Gold", "AC", "Abilities", "Proficiencies", "Magic",
        "Spell_Effects", "Inventory"
    ],
    "additionalProperties": False
}

# Monster schema
monster_schema = {
    "type": "object",
    "properties": {
        "identifier": {"type": "string"},
        "description": {"type": "string"},
        "abilities": ability_schema,
        "AC": {"type": "integer"},
        "health": {"type": "integer"},
        "status": {"type": "string"}
    },
    "required": ["identifier", "description", "abilities", "AC", "health", "status"],
    "additionalProperties": False
} 