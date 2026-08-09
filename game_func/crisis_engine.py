import json
import random

class CrisesEngine:
    # Manages crisis events based on pillar and hidden stats.
    # Tracks played crises (no repeats) and locks a crisis until resolved.
    # Includes a cooldown to prevent back-to-back crisis spam.

    def __init__(self, json_path='data/crises.json'):
        # Load crisis definitions from JSON
        try:
            with open(json_path, 'r', encoding='utf-8') as json_file:
                self.crises_data = json.load(json_file)
        except Exception as error:
            print(f"[CrisesEngine Error] Failed to load JSON file '{json_path}': {error}")
            self.crises_data = {"crises": []}

        # Set of crisis IDs already fired (prevents repetition)
        self.played_crises = set()
        # Currently active crisis; None if no crisis pending
        self.locked_crisis = None
        # Cooldown turns before a new crisis can be checked
        self.cooldown = 0

    def reset(self):
        # Clears played history, active lock, and cooldown. Call when starting a new game session.
        self.played_crises.clear()
        self.locked_crisis = None
        self.cooldown = 0

    def check_crises(self, game_state):
        # Check if any crisis should trigger based on current game state.
        # Returns the crisis dict if triggered, else None.

        # If a crisis is locked, keep returning it until resolved
        if self.locked_crisis is not None:
            return self.locked_crisis

        # Cooldown: if we recently resolved a crisis, skip checking for a few turns
        if self.cooldown > 0:
            self.cooldown -= 1
            return None

        matching = []   # Crises meeting all trigger conditions

        for crisis in self.crises_data.get('crises', []):
            crisis_id = crisis.get('id')

            # Skip already played crises
            if crisis_id in self.played_crises:
                continue

            trigger = crisis.get('trigger', {})
            trigger_type = trigger.get('type')
            conditions = trigger.get('conditions', {})

            # Standardize stats source retrieval
            pillars_dict = game_state.pillars if isinstance(game_state.pillars, dict) else vars(game_state.pillars)
            hidden_dict = game_state.hidden if isinstance(game_state.hidden, dict) else vars(game_state.hidden)

            # Choose stat source based on trigger type
            if trigger_type == 'pillar':
                stats_source = pillars_dict
            elif trigger_type == 'hidden':
                stats_source = hidden_dict
            elif trigger_type == 'combined':
                stats_source = {**pillars_dict, **hidden_dict}
            else:
                continue   # unknown trigger type – skip silently

            # Verify all conditions are met
            all_met = True
            for stat_name, threshold in conditions.items():
                current_value = stats_source.get(stat_name)

                if current_value is None:
                    all_met = False
                    break

                # If 'max' is defined, current_value must be <= max
                if 'max' in threshold and current_value > threshold['max']:
                    all_met = False
                    break

                # If 'min' is defined, current_value must be >= min
                if 'min' in threshold and current_value < threshold['min']:
                    all_met = False
                    break

            if all_met:
                matching.append(crisis)

        if not matching:
            return None

        # Lock a randomly chosen matching crisis
        self.locked_crisis = random.choice(matching)
        return self.locked_crisis

    def resolve_crisis(self, crisis_id=None):
        # Mark the current (or specified) crisis as resolved.
        # Called after the player makes a choice.
        if crisis_id:
            self.played_crises.add(crisis_id)
        elif self.locked_crisis:
            self.played_crises.add(self.locked_crisis['id'])

        # Clear the lock to allow new crises later
        self.locked_crisis = None
        # Set cooldown: 2 normal turns must pass before another crisis can be checked
        self.cooldown = 2
