import json
import os
import pygame

class DataLoader:
    # Central data management class for the GNH game.
    # Loads JSON, manages display with virtual resolution scaling, and saves persistent district progress.

    def __init__(self):
        # Initialise audio and load background music
        try:
            pygame.mixer.init()
            self.background_music = pygame.mixer.music.load("assets/sounds/bgm.wav")
            self.main_menu = pygame.image.load('assets/ui/main_menu.png')
            self.game_icon = pygame.image.load("assets/ui/icon.png")
            self.click_sound = pygame.mixer.Sound('assets/sounds/click.wav')  # Change path to your audio file
            self.click_sound.set_volume(0.5)
        except Exception as exception_error:
            print(f"Missing assets found: {exception_error}")

        # 1. Set up Virtual Canvas Dimensions (Base target aspect ratio: 16:9)
        self.VIRTUAL_WIDTH = 1366
        self.VIRTUAL_HEIGHT = 768
        self.virtual_surface = pygame.Surface((self.VIRTUAL_WIDTH, self.VIRTUAL_HEIGHT))

        # 2. Get actual screen resolution and set window mode
        display_info = pygame.display.Info()
        self.WIDTH = display_info.current_w
        self.HEIGHT = display_info.current_h

        self.screen = pygame.display.set_mode(
            (self.WIDTH, self.HEIGHT),
            pygame.FULLSCREEN | pygame.RESIZABLE
        )
        self.title = "GNH"
        pygame.display.set_caption(self.title)

        # Scale factor attributes
        self.scale = 1.0
        self.scaled_w = self.VIRTUAL_WIDTH
        self.scaled_h = self.VIRTUAL_HEIGHT
        self.offset_x = 0
        self.offset_y = 0
        self.recalculate_scale()

        # Mouse and cursor tracking
        self.selected_district = None
        self.hovered = None
        self.mousePos = pygame.mouse.get_pos()
        self.frames = 60
        self.clock = pygame.time.Clock()

        # Custom cursor
        try:
            original_mouse_sprite = pygame.image.load('assets/ui/mouse_icon.png').convert_alpha()
            mouse_sprite = pygame.transform.scale(original_mouse_sprite, (32, 32))
            self.cursor_sprite = pygame.cursors.Cursor((0, 0), mouse_sprite)
        except Exception as cursor_error:
            print(f"Cursor load warning: {cursor_error}")
            self.cursor_sprite = pygame.SYSTEM_CURSOR_ARROW

        # Load district data from JSON
        self.data = {}
        self.reload_data()

    def recalculate_scale(self):
        # Recalculates scaling factors and offset centering for letterboxing.
        scale_x = self.WIDTH / self.VIRTUAL_WIDTH
        scale_y = self.HEIGHT / self.VIRTUAL_HEIGHT

        # Maintain aspect ratio (uniform scale)
        self.scale = min(scale_x, scale_y)

        self.scaled_w = int(self.VIRTUAL_WIDTH * self.scale)
        self.scaled_h = int(self.VIRTUAL_HEIGHT * self.scale)

        # Calculate offsets to center the virtual surface on display
        self.offset_x = (self.WIDTH - self.scaled_w) // 2
        self.offset_y = (self.HEIGHT - self.scaled_h) // 2

    def get_virtual_mouse_pos(self):
        # Converts raw screen mouse coordinates to internal virtual surface coordinates.
        raw_x, raw_y = pygame.mouse.get_pos()
        virt_x = (raw_x - self.offset_x) / self.scale
        virt_y = (raw_y - self.offset_y) / self.scale

        # Clamp values within bounds of virtual canvas
        virt_x = max(0, min(self.VIRTUAL_WIDTH, virt_x))
        virt_y = max(0, min(self.VIRTUAL_HEIGHT, virt_y))

        return int(virt_x), int(virt_y)

    def render_frame(self):
        # Scales and draws the virtual surface onto the main display screen.
        self.screen.fill((0, 0, 0))  # Letterbox background color
        scaled_surface = pygame.transform.smoothscale(
            self.virtual_surface,
            (self.scaled_w, self.scaled_h)
        )
        self.screen.blit(scaled_surface, (self.offset_x, self.offset_y))

    def show_fps(self, enabled):
        if not enabled:
            return
        font = pygame.font.SysFont("Arial", 30)
        frames_per_second = str(int(self.clock.get_fps()))
        fps_rendered = font.render(frames_per_second, True, (255, 0, 0))
        # Draw directly to top-left of the display screen
        self.screen.blit(fps_rendered, (10, 10))

    def get_district_data(self):
        # Safely return data for selected district with case-insensitive fallback
        if not self.selected_district:
            print("Warning: No district selected.")
            return None

        districts = self.data.get("districts", {})

        # Direct match
        if self.selected_district in districts:
            return districts[self.selected_district]

        # Case/whitespace tolerant match fallback
        target_name = str(self.selected_district).strip().lower()
        for key, data in districts.items():
            if str(key).strip().lower() == target_name:
                return data

        print(f"Warning: Received empty district data for '{self.selected_district}'. Available keys: {list(districts.keys())}")
        return None

    def reload_data(self):
        try:
            with open("data/game_data.json", "r") as file_handle:
                self.data = json.load(file_handle)
        except Exception as reload_error:
            print(f"Error loading game_data.json: {reload_error}")
            self.data = {"districts": {}}

    def save_district_data(self, district_name, final_state):
        try:
            with open("data/game_data.json", "r") as file_handle:
                full_data = json.load(file_handle)

            # Match target district key
            target_key = None
            if district_name in full_data.get("districts", {}):
                target_key = district_name
            else:
                for key in full_data.get("districts", {}):
                    if key.strip().lower() == str(district_name).strip().lower():
                        target_key = key
                        break

            if target_key:
                full_data["districts"][target_key]["starting_gnh"] = final_state.get("starting_gnh", 50)
                full_data["districts"][target_key]["hidden_vars"] = final_state.get("hidden_vars", {})

                with open("data/game_data.json", "w") as file_handle:
                    json.dump(full_data, file_handle, indent=4)

                self.reload_data()
                print(f"Saved progress for {district_name}")
            else:
                print(f"District {district_name} not found.")
        except Exception as save_error:
            print(f"Error saving district data: {save_error}")

    def reset_all_district_data(self):
        try:
            with open("data/default_data.json", "r") as default_file:
                default_data = json.load(default_file)

            with open("data/game_data.json", "w") as file_handle:
                json.dump(default_data, file_handle, indent=4)

            self.reload_data()
            print("Successfully reset all district data.")
        except Exception as reset_error:
            print(f"Error resetting district data: {reset_error}")
