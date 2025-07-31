"""State validation and defensive merging utilities."""

import copy
import logging
from typing import Any, Dict, List, NamedTuple, Set
from ..log_config import get_logger

class ValidationResult(NamedTuple):
    """Result of state validation."""
    is_valid: bool
    issues: List[str]

class StateValidator:
    """Validates game state changes and provides defensive merging."""
    
    def __init__(self):
        self.logger = get_logger()
    
    def validate_state_changes(self, old_state: Dict[str, Any], new_state: Dict[str, Any], action_description: str) -> ValidationResult:
        """Validate that state changes are reasonable and expected.
        
        Args:
            old_state: The previous game state
            new_state: The proposed new game state
            action_description: Description of what happened during the action
            
        Returns:
            ValidationResult indicating if changes are valid and any issues found
        """
        issues = []
        
        # Validate player character changes
        player_issues = self._validate_player_changes(old_state, new_state, action_description)
        issues.extend(player_issues)
        
        # Validate inventory changes
        inventory_issues = self._validate_inventory_changes(old_state, new_state, action_description)
        issues.extend(inventory_issues)
        
        # Validate magic/spell changes
        magic_issues = self._validate_magic_changes(old_state, new_state, action_description)
        issues.extend(magic_issues)
        
        # Log validation results
        if issues:
            self.logger.warning(f"State validation found {len(issues)} issues: {issues}")
        else:
            self.logger.debug("State validation passed")
        
        return ValidationResult(len(issues) == 0, issues)
    
    def _validate_player_changes(self, old_state: Dict[str, Any], new_state: Dict[str, Any], action_description: str) -> List[str]:
        """Validate changes to player character."""
        issues = []
        
        player_old = old_state.get('player', {})
        player_new = new_state.get('player', {})
        
        if not player_old or not player_new:
            return issues
        
        # Critical fields that should rarely change
        critical_fields = ['Name', 'Race', 'Class', 'Pronouns']
        for field in critical_fields:
            if player_old.get(field) != player_new.get(field):
                # Check if the change was mentioned in the action
                old_val = player_old.get(field, '')
                new_val = player_new.get(field, '')
                if not self._change_mentioned_in_action(field, old_val, new_val, action_description):
                    issues.append(f"Unexpected change to {field}: '{old_val}' -> '{new_val}'")
        
        # Level changes should be rare and explicit
        old_level = player_old.get('Level', 1)
        new_level = player_new.get('Level', 1)
        if old_level != new_level:
            level_keywords = ['level up', 'gain level', 'advance', 'experience']
            if not any(keyword in action_description.lower() for keyword in level_keywords):
                issues.append(f"Unexpected level change: {old_level} -> {new_level}")
        
        # Ability score changes should be very rare
        old_abilities = player_old.get('Abilities', {})
        new_abilities = player_new.get('Abilities', {})
        for ability in ['Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma']:
            old_val = old_abilities.get(ability, 10)
            new_val = new_abilities.get(ability, 10)
            if old_val != new_val:
                ability_keywords = ['boost', 'enhance', 'drain', 'curse', 'magic', 'potion']
                if not any(keyword in action_description.lower() for keyword in ability_keywords):
                    issues.append(f"Unexpected {ability} change: {old_val} -> {new_val}")
        
        return issues
    
    def _validate_inventory_changes(self, old_state: Dict[str, Any], new_state: Dict[str, Any], action_description: str) -> List[str]:
        """Validate inventory changes."""
        issues = []
        
        player_old = old_state.get('player', {})
        player_new = new_state.get('player', {})
        
        old_inventory = player_old.get('Inventory', [])
        new_inventory = player_new.get('Inventory', [])
        
        # Check for gold/money items in inventory (should never happen)
        money_keywords = ['gold', 'coin', 'coins', 'gold piece', 'gold pieces', 'copper', 'silver', 'platinum', 'gp', 'cp', 'sp', 'pp']
        for item in new_inventory:
            item_lower = item.lower()
            if any(keyword in item_lower for keyword in money_keywords):
                issues.append(f"Money item '{item}' found in inventory - money should be tracked in Gold field only")
        
        # Check for duplicate items (unless explicitly acquiring multiples)
        from collections import Counter
        new_inventory_counts = Counter(new_inventory)
        old_inventory_counts = Counter(old_inventory)
        
        for item, new_count in new_inventory_counts.items():
            old_count = old_inventory_counts.get(item, 0)
            if new_count > old_count + 1:  # More than one new copy of the same item
                # Check if multiple acquisition was mentioned
                multiple_keywords = ['multiple', 'several', 'many', 'bunch', 'stack', 'pile', f'{new_count}', 'two', 'three', 'four', 'five']
                if not any(keyword in action_description.lower() for keyword in multiple_keywords):
                    issues.append(f"Unexpected duplicate items: {new_count} copies of '{item}' (was {old_count})")
        
        # Check for lost items
        old_inventory_set = set(old_inventory)
        new_inventory_set = set(new_inventory)
        lost_items = old_inventory_set - new_inventory_set
        if lost_items:
            loss_keywords = ['drop', 'sell', 'trade', 'use', 'consume', 'break', 'destroy', 'give', 'lose']
            if not any(keyword in action_description.lower() for keyword in loss_keywords):
                issues.append(f"Unexpected inventory loss: {list(lost_items)}")
        
        # Check for dramatic inventory reduction (more than 50% loss)
        if len(new_inventory_set) < len(old_inventory_set) * 0.5 and len(old_inventory_set) > 2:
            issues.append(f"Dramatic inventory reduction: {len(old_inventory_set)} -> {len(new_inventory_set)} items")
        
        return issues
    
    def _validate_magic_changes(self, old_state: Dict[str, Any], new_state: Dict[str, Any], action_description: str) -> List[str]:
        """Validate magic and spell changes."""
        issues = []
        
        player_old = old_state.get('player', {})
        player_new = new_state.get('player', {})
        
        old_magic = player_old.get('Magic', {})
        new_magic = player_new.get('Magic', {})
        
        # Check for spell knowledge changes
        old_spells = set(old_magic.get('Spells_Known', []))
        new_spells = set(new_magic.get('Spells_Known', []))
        
        if old_spells != new_spells:
            magic_keywords = ['learn', 'forget', 'teach', 'scroll', 'spellbook', 'level up']
            if not any(keyword in action_description.lower() for keyword in magic_keywords):
                lost_spells = old_spells - new_spells
                gained_spells = new_spells - old_spells
                if lost_spells:
                    issues.append(f"Unexpected spell loss: {list(lost_spells)}")
                if gained_spells:
                    issues.append(f"Unexpected spell gain: {list(gained_spells)}")
        
        # Check for cantrip changes
        old_cantrips = set(old_magic.get('Cantrips_Known', []))
        new_cantrips = set(new_magic.get('Cantrips_Known', []))
        
        if old_cantrips != new_cantrips:
            magic_keywords = ['learn', 'forget', 'teach', 'level up']
            if not any(keyword in action_description.lower() for keyword in magic_keywords):
                issues.append(f"Unexpected cantrip changes: {old_cantrips} -> {new_cantrips}")
        
        return issues
    
    def _change_mentioned_in_action(self, field: str, old_val: str, new_val: str, action_description: str) -> bool:
        """Check if a field change is mentioned in the action description."""
        action_lower = action_description.lower()
        
        # Check if old or new values are mentioned
        if old_val and old_val.lower() in action_lower:
            return True
        if new_val and new_val.lower() in action_lower:
            return True
        
        # Check for field-specific keywords
        field_keywords = {
            'Name': ['rename', 'call', 'name'],
            'Race': ['transform', 'polymorph', 'change race'],
            'Class': ['multiclass', 'change class', 'become'],
            'Pronouns': ['pronoun', 'gender']
        }
        
        keywords = field_keywords.get(field, [])
        return any(keyword in action_lower for keyword in keywords)
    
    def merge_states_defensively(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> Dict[str, Any]:
        """Merge states defensively, preserving critical fields unless explicitly changed.
        
        Args:
            old_state: The previous game state
            new_state: The proposed new game state
            
        Returns:
            Merged state with defensive preservation of critical fields
        """
        merged = copy.deepcopy(old_state)
        
        # Safe fields that can always be updated
        safe_top_level_fields = [
            'location', 'danger', 'time_of_day', 'sunrise', 'sunset', 
            'date', 'dark', 'monsters', 'NPCs'
        ]
        
        for field in safe_top_level_fields:
            if field in new_state:
                merged[field] = new_state[field]
        
        # Handle player updates carefully
        if 'player' in new_state and 'player' in old_state:
            merged['player'] = self._merge_player_defensively(old_state['player'], new_state['player'])
        
        self.logger.debug("Performed defensive state merge")
        return merged
    
    def _merge_player_defensively(self, old_player: Dict[str, Any], new_player: Dict[str, Any]) -> Dict[str, Any]:
        """Merge player data defensively."""
        merged_player = copy.deepcopy(old_player)
        
        # Safe player fields that can be updated
        safe_player_fields = [
            'HP', 'Gold', 'Status', 'XP', 'location'
        ]
        
        for field in safe_player_fields:
            if field in new_player:
                merged_player[field] = new_player[field]
        
        # Handle inventory with comprehensive validation
        if 'Inventory' in new_player:
            old_inventory = old_player.get('Inventory', [])
            new_inventory = new_player['Inventory']
            
            # Clean the new inventory of any money items
            cleaned_inventory = self._clean_inventory_of_money(new_inventory)
            
            # Remove excessive duplicates
            deduplicated_inventory = self._remove_excessive_duplicates(old_inventory, cleaned_inventory)
            
            # Size validation
            old_inv_size = len(old_inventory)
            final_inv_size = len(deduplicated_inventory)
            
            # Only update if new inventory isn't dramatically smaller
            if final_inv_size >= old_inv_size * 0.5 or old_inv_size <= 2:
                merged_player['Inventory'] = deduplicated_inventory
                if len(deduplicated_inventory) != len(new_inventory):
                    self.logger.info(f"Cleaned inventory: {len(new_inventory)} -> {len(deduplicated_inventory)} items")
            else:
                self.logger.warning(f"Rejecting inventory update: {old_inv_size} -> {final_inv_size} items")
                merged_player['Inventory'] = old_inventory
        
        # Handle spell effects (these change frequently)
        if 'Spell_Effects' in new_player:
            merged_player['Spell_Effects'] = new_player['Spell_Effects']
        
        # Preserve critical identity fields unless they look intentional
        critical_fields = ['Name', 'Race', 'Class', 'Level', 'Abilities', 'Proficiencies', 'Magic']
        for field in critical_fields:
            if field in new_player:
                # For now, be conservative and preserve old values for these critical fields
                # unless the new value looks significantly different (indicating intentional change)
                if field == 'Level':
                    # Allow level increases
                    old_level = old_player.get('Level', 1)
                    new_level = new_player.get('Level', 1)
                    if new_level >= old_level:
                        merged_player['Level'] = new_level
                elif field == 'Magic':
                    # Handle magic carefully - preserve spell slots updates but be careful with known spells
                    merged_player['Magic'] = self._merge_magic_defensively(
                        old_player.get('Magic', {}), 
                        new_player.get('Magic', {})
                    )
                else:
                    # For other critical fields, keep the old value unless it's clearly empty
                    if not old_player.get(field) and new_player.get(field):
                        merged_player[field] = new_player[field]
        
        return merged_player
    
    def _merge_magic_defensively(self, old_magic: Dict[str, Any], new_magic: Dict[str, Any]) -> Dict[str, Any]:
        """Merge magic data defensively."""
        merged_magic = copy.deepcopy(old_magic)
        
        # Always update spell slots (these change frequently in combat)
        if 'Spell_Slots' in new_magic:
            merged_magic['Spell_Slots'] = new_magic['Spell_Slots']
        
        # Be conservative with known spells and cantrips
        for spell_type in ['Spells_Known', 'Cantrips_Known']:
            if spell_type in new_magic:
                old_spells = set(old_magic.get(spell_type, []))
                new_spells = set(new_magic[spell_type])
                
                # Only allow additions or keep the same, don't allow losses unless very small list
                if len(old_spells) <= 2 or new_spells >= old_spells:
                    merged_magic[spell_type] = new_magic[spell_type]
                else:
                    self.logger.warning(f"Rejecting {spell_type} update: potential spell loss")
        
        return merged_magic
    
    def _clean_inventory_of_money(self, inventory: List[str]) -> List[str]:
        """Remove any money-related items from inventory."""
        money_keywords = ['gold', 'coin', 'coins', 'gold piece', 'gold pieces', 'copper', 'silver', 'platinum', 'gp', 'cp', 'sp', 'pp']
        cleaned_inventory = []
        
        for item in inventory:
            item_lower = item.lower()
            is_money = any(keyword in item_lower for keyword in money_keywords)
            if not is_money:
                cleaned_inventory.append(item)
            else:
                self.logger.warning(f"Removed money item from inventory: '{item}'")
        
        return cleaned_inventory
    
    def _remove_excessive_duplicates(self, old_inventory: List[str], new_inventory: List[str]) -> List[str]:
        """Remove excessive duplicate items that weren't in the original inventory."""
        from collections import Counter
        
        old_counts = Counter(old_inventory)
        new_counts = Counter(new_inventory)
        
        deduplicated = []
        
        for item in new_inventory:
            old_count = old_counts.get(item, 0)
            current_count = deduplicated.count(item)
            
            # Allow at most one new copy of any item (unless it was already duplicated)
            max_allowed = max(old_count + 1, old_count)
            
            if current_count < max_allowed:
                deduplicated.append(item)
            else:
                self.logger.warning(f"Removed excessive duplicate: '{item}' (keeping {max_allowed}, had {new_counts[item]})")
        
        return deduplicated