"""Response and state change rules prompts."""

RESPONSE_RULES = '''
After the user's turn, provide two responses in JSON format:

player_response: a description of what happened from the Player's point of view.  This should only include what the player can
see/perceive.  Do not include any game rule information here like die rolls or damage points.  This response should use
second-person to describe the player's actions and perceptions.  For example: "You search the room and find a hidden compartment"

DM_response: a description from the DM's perspective covering what happened to the player,
monsters, NPCs, and environment.  This should include all state changes and may include information that should be hidden
from the player and should be specific about damage points, time taken, etc.
'''

STATE_CHANGE_RULES = '''
Examine the given action description and determine how the game state has changed, generating the new game state in JSON based on the prior game state provided.
Only include the JSON response.  Only change pieces of the state as directed below -- leave everything else as it is in the prior state.

Player: this defines the player character and includes their current HP, according to D&D 5th Edition.  When the player takes damage, subtract the damage total from HP.  If HP reaches 0
or lower the player will die.
When the player is healed, increase HP but only up to the player's Max HP.

The Player object also tracks Gold: this is an integer value tracking the number of gold pieces the player carries.
When the player makes a purchase, subtract the purchase price from Gold.
When the player sells an item, add the sale price to Gold.
When the player finds money, add the amount to Gold.
Do not change Gold if the player is just bargaining or asking about prices.  The player must explicitly accept a deal or specify a purchase before Gold may change.

Inventory: this is a list of items that the player carries.
When the player picks up an item add it to the inventory.
If an NPC gives an item to the player, add it to the inventory.
When a player uses up an item or drop it then remove it from the inventory.
When the player makes a purchase, add the purchased item to the inventory.  Do not add an item if the player is just bargaining or browsing items.
When the player makes a sale, remove the sold item from the inventory.  Do not remove an item if the player is just bargaining.
The player must explicitly accept a deal or specify a purchase before Inventory may change.
Do not add the same item to the inventory more than once unless the player explicitly acquires multiple items.

Danger: the danger field determines how dangerous the current area is, expressed as safe, low, medium, high, or very high.

Examples:
"The player purchases the amulet for 10 gold pieces" -> subtract 10 from gold and add the amulet to inventory
"The merchant offers the amulet for 10 gold pieces" -> no change to gold or inventory.  This is just an offer that the player has not accepted.
"The player browses the shelves and notices a fine dagger.  The merchant quotes a price of 5 gold" --> No change to gold or inventory.
"The merchant accepts the player's offer of 10 gold pieces" -> subtract 10 from gold and add the item to inventory.  The offer was accepted.

Time of Day tracks the current time of day, in HH:MM format using 24-hour time.  Actions take time and the time of day should be updated accordingly.
Sunrise and Sunset should be computed based on the current date.  These should also be used to determine when it is night.
Date tracks the current month and day and should be in a form like "July 1".  This is used to determine sunset and sunrise times as well as to determine seasons.
Dark determines if the player is operating in darkness, meaning the area is dark and the player has no light or night vision ability.

Spell Effects track spells in effect that currently impact either the player or any NPCs or monsters.  Each spell effect has a remaining duration.
When time passes, deduct the minutes that pass from the duration of each spell effect.
If duration reaches or drops below 0, remove the spell effect.

If any monsters are present in the room, they should each be listed.
Each monster should have an identifier which can be used to differentiate them from other monsters also present, typically constructed by adding an adjective to the monster type.
For example "Fierce Goblin" or "Sneaky Lizard".  Monsters should also have Health, a Description, AC, ability scores, and a status indicator.
The status indicator determines if the monster has some unusual status that might affect how it behaves in combat.

Any NPCs in the room should be listed in the NPC section.
NPCs have statistics very similar to those of a player character, and each NPC has a name and pronouns.
''' 


RESPONSE_AND_STATE_CHANGE_RULES = '''
After the user's turn, provide two responses and the updated game state in JSON format:

player_response: a description of what happened from the Player's point of view.  This should only include what the player can
see/perceive.  Do not include any game rule information here like die rolls or damage points.  This response should use
second-person to describe the player's actions and perceptions.  For example: "You search the room and find a hidden compartment"

DM_response: a description from the DM's perspective covering what happened to the player,
monsters, NPCs, and environment.  This should include all state changes and may include information that should be hidden
from the player and should be specific about damage points, time taken, etc.

new_state: the updated state of the game.  Game state should be updated based on the result of the player's action,
according to the remaining rules below:

Player: this defines the player character and includes their current HP, according to D&D 5th Edition.  When the player takes damage, subtract the damage total from HP.  If HP reaches 0
or lower the player will die.
When the player is healed, increase HP but only up to the player's Max HP.

The Player object also tracks Gold: this is an integer value tracking the number of gold pieces the player carries.
When the player makes a purchase, subtract the purchase price from Gold.
When the player sells an item, add the sale price to Gold.
When the player finds money, add the amount to Gold.
Do not change Gold if the player is just bargaining or asking about prices.  The player must explicitly accept a deal or specify a purchase before Gold may change.

Inventory: this is a list of items that the player carries.
When the player picks up an item add it to the inventory.
If an NPC gives an item to the player, add it to the inventory.
When a player uses up an item or drop it then remove it from the inventory.
When the player makes a purchase, add the purchased item to the inventory.  Do not add an item if the player is just bargaining or browsing items.
When the player makes a sale, remove the sold item from the inventory.  Do not remove an item if the player is just bargaining.
The player must explicitly accept a deal or specify a purchase before Inventory may change.
Do not add the same item to the inventory more than once unless the player explicitly acquires multiple items.

Danger: the danger field determines how dangerous the current area is, expressed as safe, low, medium, high, or very high.

Examples:
"The player purchases the amulet for 10 gold pieces" -> subtract 10 from gold and add the amulet to inventory
"The merchant offers the amulet for 10 gold pieces" -> no change to gold or inventory.  This is just an offer that the player has not accepted.
"The player browses the shelves and notices a fine dagger.  The merchant quotes a price of 5 gold" --> No change to gold or inventory.
"The merchant accepts the player's offer of 10 gold pieces" -> subtract 10 from gold and add the item to inventory.  The offer was accepted.

Time of Day tracks the current time of day, in HH:MM format using 24-hour time.  Actions take time and the time of day should be updated accordingly.
Sunrise and Sunset should be computed based on the current date.  These should also be used to determine when it is night.
Date tracks the current month and day and should be in a form like "July 1".  This is used to determine sunset and sunrise times as well as to determine seasons.
Dark determines if the player is operating in darkness, meaning the area is dark and the player has no light or night vision ability.

Spell Effects track spells in effect that currently impact either the player or any NPCs or monsters.  Each spell effect has a remaining duration.
When time passes, deduct the minutes that pass from the duration of each spell effect.
If duration reaches or drops below 0, remove the spell effect.

If any monsters are present in the room, they should each be listed.
Each monster should have an identifier which can be used to differentiate them from other monsters also present, typically constructed by adding an adjective to the monster type.
For example "Fierce Goblin" or "Sneaky Lizard".  Monsters should also have Health, a Description, AC, ability scores, and a status indicator.
The status indicator determines if the monster has some unusual status that might affect how it behaves in combat.

Any NPCs in the room should be listed in the NPC section.
NPCs have statistics very similar to those of a player character, and each NPC has a name and pronouns.
''' 
