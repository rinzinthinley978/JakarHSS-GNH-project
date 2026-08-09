import json
import random

class ScenarioEngine:
    # Selects unplayed scenarios, ensuring no repeats across 15 turns.
    # Caches the selected scenario for the current turn.

    def __init__(self, json_path='data/decisions.json'):
        # Load decision definitions from JSON
        try:
            with open(json_path, 'r', encoding='utf-8') as data_file:
                self.decisions_data = json.load(data_file)
        except FileNotFoundError:
            print(f"Warning: {json_path} not found. Using empty data.")
            self.decisions_data = {"decisions": []}

        # Cache for the currently locked scenario
        self.locked_scenario = None
        self.locked_turn = None

    def filter_deck(self, current_turn, played_scenarios, flags):
        # Return the cached scenario if already locked for this turn
        if self.locked_scenario and self.locked_turn == current_turn:
            return self.locked_scenario

        current_flags = set(flags)
        all_decks = self.decisions_data.get('decisions', [])

        # Pass 1: Strict match – turn range, prerequisites, and unplayed
        strict_valid = []
        for deck in all_decks:
            if deck['id'] in played_scenarios:
                continue

            prerequisites = deck.get('prerequisites', {})
            required_flags = set(prerequisites.get('required_flags', []))
            forbidden_flags = set(prerequisites.get('forbidden_flags', []))

            min_turn = prerequisites.get('min_turn', 0)
            max_turn = prerequisites.get('max_turn', 999)

            if min_turn <= current_turn <= max_turn:
                if required_flags <= current_flags and forbidden_flags.isdisjoint(current_flags):
                    strict_valid.append(deck)

        if strict_valid:
            return self._lock_and_return(random.choice(strict_valid), current_turn)

        # Pass 2: Relaxed – only turn range and unplayed (ignore flags)
        turn_valid = [
            deck for deck in all_decks
            if deck['id'] not in played_scenarios
            and deck.get('prerequisites', {}).get('min_turn', 0) <= current_turn
            and current_turn <= deck.get('prerequisites', {}).get('max_turn', 999)
        ]

        if turn_valid:
            return self._lock_and_return(random.choice(turn_valid), current_turn)

        # Pass 3: Global fallback – any unplayed scenario
        global_unplayed = [deck for deck in all_decks if deck['id'] not in played_scenarios]

        if global_unplayed:
            return self._lock_and_return(random.choice(global_unplayed), current_turn)

        # All scenarios exhausted
        self.locked_scenario = None
        self.locked_turn = current_turn
        return None

    def _lock_and_return(self, scenario, turn):
        # Cache the scenario for the current turn
        self.locked_scenario = scenario
        self.locked_turn = turn
        return scenario

    def clear_lock(self):
        # Unlock the cache after a choice is made
        self.locked_scenario = None
        self.locked_turn = None
