import copy

class GameState:
    # Manages turn progression, GNH pillars, hidden stats, event flags,
    # and historical snapshots.

    def __init__(self, data_loader_instance):
        self.data_loader = data_loader_instance
        self.reset()

    def reset(self):
        # Resets all gameplay variables to starting state.
        self.turn = 0  # Start at Turn 0 (Year 0, Phase 1)
        self.yearly_snapshots = []
        self.history = []
        self.flags = set()
        self.pending_effects = []
        self.last_feedback = ""
        self.played_scenarios = set()

        self.pillars = {}
        self.hidden = {}

    def receive_data(self, district_data):
        # Initializes district-specific GNH pillar and hidden stat values.
        if not district_data:
            print("Warning: Received empty district data.")
            return

        # Extract pillar values from nested structures or fallback keys
        if "starting_gnh" in district_data:
            gnh_source = district_data["starting_gnh"]
        elif "pillars" in district_data:
            gnh_source = district_data["pillars"]
        else:
            gnh_source = district_data

        # Extract hidden variables from nested structures or fallback keys
        if "hidden_vars" in district_data:
            hidden_source = district_data["hidden_vars"]
        elif "hidden" in district_data:
            hidden_source = district_data["hidden"]
        else:
            hidden_source = district_data

        self.pillars = {
            "economy": float(gnh_source.get("economy", 50)),
            "environment": float(gnh_source.get("environment", 50)),
            "culture": float(gnh_source.get("culture", 50)),
            "governance": float(gnh_source.get("governance", 50))
        }

        self.hidden = {
            "social_unrest": float(hidden_source.get("social_unrest", 0)),
            "ecological_stress": float(hidden_source.get("ecological_stress", 0)),
            "corruption_index": float(hidden_source.get("corruption_index", 0)),
            "foreign_influence": float(hidden_source.get("foreign_influence", 0)),
            "public_trust": float(hidden_source.get("public_trust", 50))
        }

        self.record_snapshot()

    def get_gnh(self):
        # Calculates the overall GNH Index as an average of the four pillars.
        if not self.pillars:
            return 0.0
        return sum(self.pillars.values()) / 4.0

    def get_year(self):
        # Computes current game year (3 turns per year).
        return ((self.turn - 1) // 3) + 1

    def record_snapshot(self):
        # Records current turn stats into history for graphing and UI summaries.
        if not self.pillars:
            return

        snapshot = {
            'turn': self.turn,
            'year': self.get_year(),
            'economy': round(self.pillars.get('economy', 0), 1),
            'environment': round(self.pillars.get('environment', 0), 1),
            'culture': round(self.pillars.get('culture', 0), 1),
            'governance': round(self.pillars.get('governance', 0), 1),
            'gnh_index': round(self.get_gnh(), 1)
        }

        # Update current turn record or append new turn entry
        if self.history and self.history[-1]['turn'] == self.turn:
            self.history[-1] = snapshot
        else:
            self.history.append(snapshot)

    def apply_passive_decay(self):
        # Applies passive stat penalties when hidden stress variables exceed thresholds.
        if not self.pillars or not self.hidden:
            return

        # High corruption degrades governance
        if self.hidden.get('corruption_index', 0) > 50:
            decay = (self.hidden['corruption_index'] - 50) // 10
            self.pillars['governance'] = max(0.0, self.pillars['governance'] - decay)

        # Low public trust degrades culture
        if self.hidden.get('public_trust', 50) < 30:
            decay = (30 - self.hidden['public_trust']) // 5
            self.pillars['culture'] = max(0.0, self.pillars['culture'] - decay)

        # Ecological stress harms the environment
        if self.hidden.get('ecological_stress', 0) > 60:
            decay = (self.hidden['ecological_stress'] - 60) // 5
            self.pillars['environment'] = max(0.0, self.pillars['environment'] - decay)

        # Social unrest damages governance and economy
        if self.hidden.get('social_unrest', 0) > 60:
            decay = (self.hidden['social_unrest'] - 60) // 5
            self.pillars['governance'] = max(0.0, self.pillars['governance'] - decay)
            self.pillars['economy'] = max(0.0, self.pillars['economy'] - decay)

        # High foreign influence degrades culture and governance
        if self.hidden.get('foreign_influence', 0) > 70:
            decay = (self.hidden['foreign_influence'] - 70) // 5
            self.pillars['culture'] = max(0.0, self.pillars['culture'] - decay)
            self.pillars['governance'] = max(0.0, self.pillars['governance'] - decay)

    def apply_choice(self, choice_effects, is_crisis=False):
        # Applies chosen scenario choice effects and advances game time.
        if not choice_effects:
            return

        effects = choice_effects.get('effects', choice_effects)

        # Apply pillar adjustments (clamped between 0 and 100)
        if 'pillars' in effects:
            for stat, delta in effects['pillars'].items():
                if stat in self.pillars:
                    self.pillars[stat] = max(0.0, min(100.0, self.pillars[stat] + delta))

        # Apply hidden stat adjustments (clamped between 0 and 100)
        if 'hidden' in effects:
            for stat, delta in effects['hidden'].items():
                if stat in self.hidden:
                    self.hidden[stat] = max(0.0, min(100.0, self.hidden[stat] + delta))

        # Update event flags
        # IMPORTANT: Flags live at the TOP LEVEL of the choice dict, not inside 'effects'.
        # JSON keys are 'set_flags' and 'remove_flags'.
        if 'set_flags' in choice_effects:
            self.flags.update(choice_effects['set_flags'])
        if 'remove_flags' in choice_effects:
            self.flags.difference_update(choice_effects['remove_flags'])

        if not is_crisis:
            self.apply_passive_decay()

            # Record year snapshot before advancing turn on year boundaries
            if self.turn % 3 == 0:
                self.save_snapshot()

            self.turn += 1

        self.record_snapshot()

    def save_snapshot(self):
        # Stores a snapshot at the end of each game year.
        snapshot = {
            "year": self.get_year(),
            "pillars": copy.deepcopy(self.pillars),
            "gnh": round(self.get_gnh(), 1)
        }
        self.yearly_snapshots.append(snapshot)

    def update_scenario_details(self, scenario_id):
        # Registers a played scenario ID to avoid repetition.
        self.played_scenarios.add(scenario_id)

    def get_final_state(self):
        # Returns a clean copy of the current state for save systems or post-game reports.
        return {
            "starting_gnh": copy.deepcopy(self.pillars),
            "hidden_vars": copy.deepcopy(self.hidden),
            "played_scenarios": list(self.played_scenarios),
            "flags": list(self.flags)
        }
