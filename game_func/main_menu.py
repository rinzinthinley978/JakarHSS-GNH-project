import json
import os
import pygame

class MainMenu:
    # Main menu using DataLoader's unified virtual resolution surface or direct display targeting.
    # Anchors buttons dynamically to the bottom-left corner.

    def __init__(self, data_loader, heading_font, body_font, click_sound=None):
        self.data_loader = data_loader
        self.heading_font = heading_font
        self.body_font = body_font
        self.click_sound = click_sound

        # Reference virtual canvas sizes directly from DataLoader
        self.VIRTUAL_W = getattr(self.data_loader, 'VIRTUAL_WIDTH', self.data_loader.WIDTH)
        self.VIRTUAL_H = getattr(self.data_loader, 'VIRTUAL_HEIGHT', self.data_loader.HEIGHT)

        # Load background
        try:
            background_image = pygame.image.load("assets/ui/main_menu.png").convert_alpha()
            self.background_image = pygame.transform.scale(background_image, (self.VIRTUAL_W, self.VIRTUAL_H))
        except Exception:
            self.background_image = pygame.Surface((self.VIRTUAL_W, self.VIRTUAL_H))
            self.background_image.fill((25, 35, 45))

        # Default fallback button texture
        try:
            self.button_texture = pygame.image.load("assets/ui/button.png").convert_alpha()
        except Exception:
            self.button_texture = None

        # Load menu config
        config_path = "assets/ui/menu_config.json"
        try:
            with open(config_path, "r") as config_file:
                self.menu_config = json.load(config_file)
        except (FileNotFoundError, json.JSONDecodeError):
            button_width, button_height = 300, 100
            self.menu_config = {
                "theme": {
                    "text_color": [255, 253, 208],
                    "hover_color": [255, 255, 255]
                },
                "buttons": [
                    {"id": "start_game", "text": "START GAME", "width": button_width, "height": button_height, "image": "assets/ui/start_button.png"},
                    {"id": "reset",      "text": "Reset Data", "width": button_width, "height": button_height, "image": "assets/ui/reset_button.png"},
                    {"id": "quit",       "text": "EXIT GAME", "width": button_width, "height": button_height, "image": "assets/ui/quit_button.png"}
                ]
            }

        self.colors = self.menu_config["theme"]
        self.buttons_data = self.menu_config["buttons"]

        # Load individual button images (if specified in config or assigned manually)
        for button in self.buttons_data:
            image_path = button.get("image")
            if image_path and os.path.exists(image_path):
                try:
                    button["texture"] = pygame.image.load(image_path).convert_alpha()
                except Exception as e:
                    print(f"Failed to load button image '{image_path}': {e}")
                    button["texture"] = None
            else:
                button["texture"] = None

        # Recalculate positions to ensure bottom-left alignment
        margin_x = 20
        margin_bottom = 20
        spacing = 6
        total_height = sum(button["height"] for button in self.buttons_data) + spacing * (len(self.buttons_data) - 1)
        start_y = self.VIRTUAL_H - margin_bottom - total_height

        current_y = start_y
        for button in self.buttons_data:
            button["x"] = margin_x
            button["y"] = current_y
            current_y += button["height"] + spacing

        # Render title once
        self.title_text = "GAKI PELZOM"
        self.title_shadow = self.heading_font.Font(self.title_text, (20, 15, 5), 80)
        self.title_surface = self.heading_font.Font(self.title_text, (10, 215, 10), 79)

    def get_mouse_pos(self):
        # Returns transformed mouse position matching canvas scale.
        if hasattr(self.data_loader, 'get_virtual_mouse_pos'):
            return self.data_loader.get_virtual_mouse_pos()
        return pygame.mouse.get_pos()

    def draw(self, target_surface=None):
        # Draw the main menu onto target surface or main display screen.
        if target_surface:
            surface = target_surface
        elif hasattr(self.data_loader, 'virtual_surface') and self.data_loader.virtual_surface:
            surface = self.data_loader.virtual_surface
        else:
            surface = self.data_loader.screen

        surface.blit(self.background_image, (0, 0))

        # Title positioned top-center near top of screen
        title_y = int(self.VIRTUAL_H * 0.1)
        center_x = int(self.VIRTUAL_W // 2)
        title_rect = self.title_surface.get_rect(center=(center_x, title_y))
        shadow_rect = self.title_shadow.get_rect(center=(center_x + 2, title_y + 2))

        surface.blit(self.title_shadow, shadow_rect)
        surface.blit(self.title_surface, title_rect)

        # Get mouse position
        mouse_x, mouse_y = self.get_mouse_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        # Draw buttons
        for button in self.buttons_data:
            button_rect = pygame.Rect(button["x"], button["y"], button["width"], button["height"])
            is_hovered = button_rect.collidepoint((mouse_x, mouse_y))
            is_pressed = is_hovered and mouse_pressed

            if is_pressed:
                draw_rect = button_rect.move(1, 2)
            elif is_hovered:
                draw_rect = button_rect.move(0, -1)
            else:
                draw_rect = button_rect

            draw_pos = (int(draw_rect.x), int(draw_rect.y))

            # --- OPTION 1: SPECIFIC CUSTOM BUTTON IMAGE ---
            btn_texture = button.get("texture") or self.button_texture

            if btn_texture:
                scaled_button = pygame.transform.scale(btn_texture, (button["width"], button["height"]))

                if is_pressed:
                    pressed_texture = scaled_button.copy()
                    pressed_texture.fill((50, 50, 50), special_flags=pygame.BLEND_RGB_SUB)
                    surface.blit(pressed_texture, draw_pos)
                elif is_hovered:
                    hover_texture = scaled_button.copy()
                    hover_texture.fill((30, 30, 30), special_flags=pygame.BLEND_RGB_ADD)
                    surface.blit(hover_texture, draw_pos)
                else:
                    surface.blit(scaled_button, draw_pos)

            # --- OPTION 2: FALLBACK COLOR RECTANGLE ---
            else:
                background_color = (130, 80, 35) if is_pressed else ((160, 110, 55) if is_hovered else (92, 58, 33))
                pygame.draw.rect(surface, background_color, draw_rect, border_radius=4)

            # Render Button Text (Optional if text is baked into the image, otherwise renders on top)
            if button.get("text"):
                text_color = (255, 215, 0) if is_pressed else (self.colors.get("hover_color", [255, 255, 255]) if is_hovered else self.colors["text_color"])
                text_surface = self.body_font.Font(button["text"], text_color, 40)
                text_rect = text_surface.get_rect(center=draw_rect.center)
                surface.blit(text_surface, text_rect)

    def handle_events(self, event):
        # Process events and return an action string.
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            mouse_x, mouse_y = self.get_mouse_pos()

            for button in self.buttons_data:
                button_rect = pygame.Rect(button["x"], button["y"], button["width"], button["height"])
                if button_rect.collidepoint((mouse_x, mouse_y)):
                    if self.click_sound:
                        self.click_sound.play()

                    if button["id"] == "start_game":
                        return "start"
                    elif button["id"] == "reset":
                        return "reset"
                    elif button["id"] == "quit":
                        return "quit"
        return None
