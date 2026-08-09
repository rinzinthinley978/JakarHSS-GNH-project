import pygame
import random
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.backends.backend_agg as agg


class GameScene:

    def __init__(self, data_loader_instance, panel_instance, heading_font_instance, body_font_instance):
        self.data_loader = data_loader_instance
        self.mousePos = self.data_loader.mousePos
        self.panel = panel_instance
        self.heading_font = heading_font_instance
        self.body_font = body_font_instance
        self.screen = self.data_loader.screen

        self.width = self.data_loader.WIDTH
        self.height = self.data_loader.HEIGHT

        quadrant_w = self.width // 2
        quadrant_h = self.height // 2
        padding = 20

        self.zone_top_left = pygame.Rect(0, 0, quadrant_w, quadrant_h)
        self.zone_top_right = pygame.Rect(self.width // 2 - padding, padding, self.width - quadrant_w, quadrant_h)

        try:
            info_panel_surface = pygame.image.load('assets/ui/panel.png').convert_alpha()
        except Exception:
            info_panel_surface = pygame.Surface((quadrant_w, quadrant_h))
            info_panel_surface.fill((40, 40, 40))

        self.info_panel = pygame.transform.scale(info_panel_surface, (quadrant_w - padding, quadrant_h - padding))
        self.info_panel_rect = self.info_panel.get_rect(center=self.zone_top_left.center)

        self.max_turns = 15
        self.choice_buttons = []

        self.initial_spin_time = 3.0
        self.update_spin_time = 1.0
        self.flip_speed = 0.04
        self.sound_rhythm = 0.05

        self.counters = {}
        self.last_sound_time = 0.0

        self.click_cooldown = 1.0
        self.last_click_time = 0.0

        self.scenario_locked = True

        self.ghost_active = False
        self.ghost_start_time = 0.0
        self.ghost_duration = 2.0
        self.ghost_selected_index = None
        self.ghost_feedback_text = ""
        self.ghost_scenario_title = ""

        self.pillar_colors = {
            'economy': '#E74C3C',
            'environment': '#2ECC71',
            'culture': '#F39C12',
            'governance': '#3498DB',
            'gnh_index': '#9B59B6'
        }

        self.option_colors = []

        self.click_sound = self.create_sound(freq_start=1800, freq_end=320, duration=0.025, volume=0.25)
        self.lock_sound = self.create_sound(freq_start=400, freq_end=80, duration=0.05, volume=0.35)

        try:
            self.end_sound = pygame.mixer.Sound('assets/sounds/success.wav')
        except Exception:
            self.end_sound = self.create_sound(freq_start=400, freq_end=1200, duration=2.0, volume=0.25)
        self.end_sound_played = False
        self.end_sound.set_volume(0.5)

        try:
            back_raw = pygame.image.load('assets/ui/back_button.png').convert_alpha()
        except Exception:
            back_raw = pygame.Surface((50, 50), pygame.SRCALPHA)
            back_raw.fill((200, 50, 50))
        self.back_button = pygame.transform.scale(back_raw, (50, 50))

        self.back_rect = self.back_button.get_rect(topleft=(10, 10))

        self._shuffled_options = None
        self._last_scenario_id = None
        self._ghost_shuffled_options = None

    def reset(self):
        self.counters = {}
        self.last_sound_time = 0.0
        self.last_click_time = 0.0
        self.scenario_locked = True
        self.option_colors = []
        self.choice_buttons = []
        self.ghost_active = False
        self.ghost_start_time = 0.0
        self.ghost_selected_index = None
        self.ghost_feedback_text = ""
        self.ghost_scenario_title = ""
        self._shuffled_options = None
        self._last_scenario_id = None
        self._ghost_shuffled_options = None
        self.end_sound_played = False

    def create_sound(self, freq_start, freq_end, duration, volume):
        sample_rate = 44100
        total_samples = int(sample_rate * duration)
        t = np.linspace(0, duration, total_samples, False)
        frequencies = np.linspace(freq_start, freq_end, total_samples)
        wave = np.sin(2 * np.pi * frequencies * t) * np.exp(-t * (100 / duration))
        stereo_wave = np.vstack((wave, wave)).T
        max_val = np.max(np.abs(stereo_wave))
        if max_val > 0:
            stereo_wave = stereo_wave / max_val
        audio_bytes = (stereo_wave * 32767 * volume).astype(np.int16).tobytes()
        return pygame.mixer.Sound(buffer=audio_bytes)

    def render_matplotlib_graph(self, history, width=800, height=450):
        dpi = 100
        fig_w = width / dpi
        fig_h = height / dpi

        fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
        try:
            fig.patch.set_facecolor('#fff0f1')
            ax.set_facecolor('#FFFFFF')

            turns = [entry['turn'] for entry in history] if history else [0]
            keys = ['economy', 'environment', 'culture', 'governance', 'gnh_index']
            labels = {
                'economy': 'Economy',
                'environment': 'Environment',
                'culture': 'Culture',
                'governance': 'Governance',
                'gnh_index': 'GNH Index'
            }

            for key in keys:
                data = [entry.get(key, 50) for entry in history] if history else [50]
                linewidth = 3.0 if key == 'gnh_index' else 1.8
                linestyle = '-' if key == 'gnh_index' else '--'

                ax.plot(
                    turns, data,
                    label=labels[key],
                    color=self.pillar_colors[key],
                    linewidth=linewidth,
                    linestyle=linestyle,
                    marker='o',
                    markersize=4
                )

            ax.set_title("15-Turn Gross National Happiness Trajectory", fontsize=14, fontweight='bold', pad=10)
            ax.set_xlim(0, self.max_turns)
            ax.set_ylim(0, 100)
            ax.set_xlabel("Turn", fontsize=11)
            ax.set_ylabel("Score", fontsize=11)
            ax.tick_params(axis='both', which='major', labelsize=9)
            ax.grid(True, linestyle=':', alpha=0.6)
            ax.legend(loc='lower right', fontsize=9, frameon=True)

            plt.tight_layout()

            canvas = agg.FigureCanvasAgg(fig)
            canvas.draw()

            buf = canvas.buffer_rgba()
            size = canvas.get_width_height()
            surf = pygame.image.frombuffer(buf, size, "RGBA")
            return surf
        finally:
            plt.close(fig)

    def draw_end_screen(self, gameState):
        self.screen.fill('#fff0f1')

        if not self.end_sound_played:
            self.end_sound.play()
            self.end_sound_played = True

        title_surf = self.heading_font.Font("5-Year Report", 'black', 60)
        title_rect = title_surf.get_rect(center=(self.width // 2, 50))
        self.screen.blit(title_surf, title_rect)

        final_gnh = gameState.get_gnh()
        score_surf = self.body_font.Font(f"Final GNH Score: {final_gnh:.1f} / 100", '#1B7A3F', 50)
        score_rect = score_surf.get_rect(center=(self.width // 2, 120))
        self.screen.blit(score_surf, score_rect)

        if final_gnh >= 80:
            grade, color = "Excellent! A model of happiness.", (60, 180, 80)
        elif final_gnh >= 60:
            grade, color = "Good, but there's room for improvement.", (220, 160, 20)
        elif final_gnh >= 40:
            grade, color = "Struggling. Hard choices ahead.", (220, 120, 20)
        else:
            grade, color = "Critical. The people are suffering.", (220, 60, 60)

        grade_surf = self.body_font.Font(grade, color, 35)
        grade_rect = grade_surf.get_rect(center=(self.width // 2, 175))
        self.screen.blit(grade_surf, grade_rect)

        pillars = gameState.pillars
        pillar_labels = {"economy": "Economy", "environment": "Environment", "culture": "Culture", "governance": "Governance"}
        pillar_colors = {"economy": (220, 60, 60), "environment": (60, 180, 80), "culture": (220, 160, 20), "governance": (60, 120, 220)}

        panel_w, panel_h = 250, 280
        panel_x = self.width - panel_w - 40
        panel_y = (self.height - panel_h) // 2

        y_offset = panel_y + 20
        font_size = 32
        for key, label in pillar_labels.items():
            value = pillars.get(key, 0)
            text = f"{label}: {int(value)}"
            text_surf = self.body_font.Font(text, pillar_colors[key], font_size)
            text_rect = text_surf.get_rect(centerx=panel_x + panel_w // 2, top=y_offset)
            self.screen.blit(text_surf, text_rect)
            y_offset += font_size + 12

        history = getattr(gameState, 'history', [])
        graph_w = self.width - panel_w - 100
        graph_h = self.height - 220
        graph_surf = self.render_matplotlib_graph(history, width=graph_w, height=graph_h)
        graph_rect = graph_surf.get_rect(center=(graph_w // 2 + 30, self.height // 2 + 40))
        self.screen.blit(graph_surf, graph_rect)

        self.screen.blit(self.back_button, self.back_rect)

    def display_info(self, game_state_instance):
        self.screen.blit(self.info_panel, self.info_panel_rect)

        pillars_info = {
            "economy": game_state_instance.pillars.get("economy", 50),
            "environment": game_state_instance.pillars.get("environment", 50),
            "culture": game_state_instance.pillars.get("culture", 50),
            "governance": game_state_instance.pillars.get("governance", 50)
        }

        x_offset = self.info_panel_rect.x + 35
        y_offset = self.info_panel_rect.y + 35
        line_height = 70
        current_time = pygame.time.get_ticks() / 1000.0
        should_play_click = False
        all_spinning_done = True

        for key, value in pillars_info.items():
            target_number = int(value)

            if key not in self.counters:
                self.counters[key] = {
                    "target": target_number,
                    "display_text": f"{target_number:03d}",
                    "start_time": current_time,
                    "last_flip_time": current_time,
                    "spin_duration": self.initial_spin_time,
                    "is_spinning": True
                }

            elif self.counters[key]["target"] != target_number and not self.counters[key]["is_spinning"]:
                self.counters[key]["target"] = target_number
                self.counters[key]["start_time"] = current_time
                self.counters[key]["last_flip_time"] = current_time
                self.counters[key]["spin_duration"] = self.update_spin_time
                self.counters[key]["is_spinning"] = True

            counter = self.counters[key]

            if counter["is_spinning"]:
                time_elapsed = current_time - counter["start_time"]
                all_spinning_done = False

                if time_elapsed >= counter["spin_duration"]:
                    counter["display_text"] = f"{counter['target']:03d}"
                    counter["is_spinning"] = False
                    self.lock_sound.play()

                elif current_time - counter["last_flip_time"] >= self.flip_speed:
                    counter["last_flip_time"] = current_time
                    counter["display_text"] = f"{random.randint(0, 100):03d}"
                    should_play_click = True

            disp_name = key.capitalize()
            info = f'{disp_name}: {counter["display_text"]}'
            text = self.body_font.Font(info, '#1B7A3F', 45)
            self.screen.blit(text, (x_offset, y_offset))

            y_offset += line_height

        if should_play_click and (current_time - self.last_sound_time >= self.sound_rhythm):
            self.click_sound.play()
            self.last_sound_time = current_time

        if all_spinning_done and self.scenario_locked:
            self.scenario_locked = False

    def draw_scenario(self, scenario, hover_index=None):
        self.choice_buttons = []

        current_time = pygame.time.get_ticks() / 1000.0
        if self.ghost_active:
            ghost_elapsed = current_time - self.ghost_start_time
            if ghost_elapsed >= self.ghost_duration:
                self.ghost_active = False
                self.ghost_selected_index = None
            else:
                self._draw_ghost_state(scenario)
                return

        if scenario is None:
            return

        title = scenario.get('title', 'Scenario')
        description = scenario.get('description', '')

        title_text = self.heading_font.wrap_text(title, 'black', 45, self.width // 2 - 40)
        title_text_rect = title_text.get_rect(midtop=self.zone_top_right.midtop)

        options = scenario.get('options', [])
        if self._last_scenario_id != scenario.get('id') or self._shuffled_options is None:
            self._shuffled_options = options.copy()
            random.shuffle(self._shuffled_options)
            self._last_scenario_id = scenario.get('id')
        shuffled_options = self._shuffled_options

        self.opts_num = max(len(shuffled_options), 1)
        opt_width = self.width // self.opts_num
        box_w = opt_width - 20
        box_h = self.height // 2 - 20
        x_shift = 0

        if len(self.option_colors) != len(shuffled_options):
            palette = [(220, 60, 60), (60, 120, 220), (60, 180, 80)]
            self.option_colors = random.sample(palette, min(len(palette), len(shuffled_options)))
            while len(self.option_colors) < len(shuffled_options):
                self.option_colors.append(random.choice(palette))

        for i, opts in enumerate(shuffled_options):
            text = opts['text']
            opts_zone = pygame.Rect(x_shift, self.height // 2, opt_width, self.height // 2)

            self.choice_buttons.append({
                'rect': opts_zone,
                'data': opts,
                'original_index': options.index(opts) if opts in options else i
            })

            box_color = self.option_colors[i]
            box_rect = pygame.Rect(x_shift + 10, self.height // 2 + 10, box_w, box_h)
            pygame.draw.rect(self.screen, box_color, box_rect, border_radius=20)

            opts_text = self.body_font.wrap_text(text, 'white', 32, opt_width - 30)
            text_rect = opts_text.get_rect(center=box_rect.center)
            self.screen.blit(opts_text, text_rect)
            x_shift += opt_width

        self.screen.blit(title_text, title_text_rect)

        if hover_index is not None and hover_index < len(shuffled_options):
            advisors = shuffled_options[hover_index].get('advisors')
            if advisors:
                advice_y = title_text_rect.bottom + 20
                max_advice_width = self.zone_top_right.width - 20
                for role, advice in advisors.items():
                    advice_quote = f"{role.capitalize()}: {advice}"
                    advice_surf = self.body_font.wrap_text(advice_quote, 'black', 30, max_advice_width)
                    advice_rect = advice_surf.get_rect(centerx=self.zone_top_right.centerx, top=advice_y)
                    self.screen.blit(advice_surf, advice_rect)
                    advice_y += advice_surf.get_height() + 10
        else:
            story_text = self.body_font.wrap_text(description, 'black', 30, self.zone_top_right.width - 40)
            story_rect = story_text.get_rect(centerx=self.zone_top_right.centerx, top=title_text_rect.bottom + 20)
            self.screen.blit(story_text, story_rect)

    def _draw_ghost_state(self, scenario):
        current_time = pygame.time.get_ticks() / 1000.0
        ghost_elapsed = current_time - self.ghost_start_time
        alpha = max(0, 255 - int((ghost_elapsed / self.ghost_duration) * 200))

        title_text = self.heading_font.wrap_text(self.ghost_scenario_title, 'black', 45, self.width // 2 - 40)
        title_text_rect = title_text.get_rect(midtop=self.zone_top_right.midtop)
        self.screen.blit(title_text, title_text_rect)

        options = self._ghost_shuffled_options if self._ghost_shuffled_options is not None else (scenario.get('options', []) if scenario else [])

        opt_width = self.width // max(len(options), 1)
        box_w = opt_width - 20
        box_h = self.height // 2 - 20
        x_shift = 0

        for i, opts in enumerate(options):
            box_rect = pygame.Rect(x_shift + 10, self.height // 2 + 10, box_w, box_h)
            if i == self.ghost_selected_index:
                ghost_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
                ghost_surf.fill((255, 255, 255, alpha))
                pygame.draw.rect(self.screen, (180, 180, 180), box_rect, border_radius=20)
                self.screen.blit(ghost_surf, box_rect)
            else:
                pygame.draw.rect(self.screen, (200, 200, 200), box_rect, border_radius=20)

            opts_text = self.body_font.wrap_text(opts['text'], 'white', 32, opt_width - 30)
            text_rect = opts_text.get_rect(center=box_rect.center)
            self.screen.blit(opts_text, text_rect)
            x_shift += opt_width

        if self.ghost_feedback_text:
            feedback_surf = self.body_font.wrap_text(self.ghost_feedback_text, '#1B7A3F', 35, self.zone_top_right.width - 40)
            feedback_rect = feedback_surf.get_rect(center=self.zone_top_right.center)
            self.screen.blit(feedback_surf, feedback_rect)

    def trigger_ghost(self, selected_option, scenario_title, shuffled_options=None):
        self.ghost_active = True
        self.ghost_start_time = pygame.time.get_ticks() / 1000.0
        self.ghost_selected_index = selected_option
        self.ghost_scenario_title = scenario_title
        self._ghost_shuffled_options = shuffled_options
        self.ghost_feedback_text = "Decision recorded. Processing consequences..."

    def set_ghost_feedback(self, text):
        self.ghost_feedback_text = text

    def handle_choice(self, event, mousePos):
        if self.ghost_active or self.scenario_locked:
            return None

        current_time = pygame.time.get_ticks() / 1000.0
        if current_time - self.last_click_time < self.click_cooldown:
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, button in enumerate(self.choice_buttons):
                if button['rect'].collidepoint(mousePos):
                    self.last_click_time = current_time
                    self.selected_choice = button['data']
                    shuffled = self._shuffled_options
                    self.trigger_ghost(i, "", shuffled)
                    return button['data']

        return None

    def handle_hover(self, mousePos=None):
        current_pos = pygame.mouse.get_pos()
        if not hasattr(self, 'choice_buttons') or not self.choice_buttons:
            return None
        for i, button in enumerate(self.choice_buttons):
            if button['rect'].collidepoint(current_pos):
                return i
        return None
