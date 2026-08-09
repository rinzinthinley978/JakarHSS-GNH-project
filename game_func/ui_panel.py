import pygame


class Panel:
    def __init__(self, data_loader_instance, heading_font_instance, body_font_instance):
        self.dl = data_loader_instance
        self.heading = heading_font_instance
        self.body = body_font_instance
        self.screen = self.dl.screen
        self.padding = 10

        # Load UI assets
        try:
            self.info_panel_surface = pygame.image.load('assets/ui/panel.png').convert_alpha()
            self.button_surface = pygame.image.load('assets/ui/button.png').convert_alpha()
            self.back_button_surface = pygame.image.load('assets/ui/back_button.png').convert_alpha()
        except Exception as e:
            print(f"Error loading UI assets: {e}")
            self.info_panel_surface = pygame.Surface((106, 122), pygame.SRCALPHA)
            self.button_surface = pygame.Surface((106, 122), pygame.SRCALPHA)
            self.back_button_surface = pygame.Surface((120, 50), pygame.SRCALPHA)

            self.info_panel_surface.fill((50, 50, 50))
            self.button_surface.fill((100, 100, 100))
            self.back_button_surface.fill((200, 50, 50))

        self.width = self.dl.WIDTH
        self.height = self.dl.HEIGHT

        self.margin_x = self.padding * (self.width / 1366)
        self.margin_y = self.padding * (self.height / 768)

        # Static Back Button Setup (Top-Left at 10,10)
        self.back_button = pygame.transform.scale(self.back_button_surface, (50, 50))
        self.back_rect = self.back_button.get_rect(topleft=(10, 10))

        # Static Begin Button Setup (Bottom-Right)
        self.button = pygame.transform.scale(self.button_surface, (200, 50))
        self.button_rect = self.button.get_rect(
            bottomright=(int(self.width - 2 * self.margin_x), int(self.height - 2 * self.margin_y))
        )
        self.begin_text = self.body.Font('BEGIN', (255, 255, 255), 45)
        self.begin_text_rect = self.begin_text.get_rect(center=self.button_rect.center)

        self.max_width = self.width - int(2 * self.margin_x)
        self.max_height = self.height - int(2 * self.margin_y)

        # Caching state tracking
        self.cached_district = None
        self.cached_lines = []
        self.info_panel: pygame.Surface | None = None
        self.info_panel_rect: pygame.Rect | None = None

    def _rebuild_panel_cache(self, district_name):
        """Rebuilds text lines and rescales the panel surface only when the district selection changes."""
        district_data = self.dl.get_district_data()
        if not district_data:
            self.cached_lines = []
            self.info_panel = None
            self.info_panel_rect = None
            return

        population = district_data.get("population", "N/A")
        description = district_data.get("description", "No description available.")

        starting_gnh = district_data.get("starting_gnh", {})
        econ = starting_gnh.get("economy", district_data.get("economy", "N/A"))
        env = starting_gnh.get("environment", district_data.get("environment", "N/A"))
        cul = starting_gnh.get("culture", district_data.get("culture", "N/A"))
        gov = starting_gnh.get("governance", district_data.get("governance", "N/A"))

        name_surf = self.heading.Font(str(district_name), 'black', 36)
        pop_surf = self.body.Font(f"Population: {population}", (60, 60, 60), 24)
        stats_surf = self.body.Font(f"Econ: {econ} | Env: {env} | Cul: {cul} | Gov: {gov}", (30, 30, 100), 24)

        base_width = max(name_surf.get_width(), pop_surf.get_width(), stats_surf.get_width()) + int(self.margin_x * 2)
        wrap_width = min(self.max_width - 20, max(base_width, 240))

        desc_surf = self.body.wrap_text(
            description,
            (40, 40, 40),
            23,
            wrap_width,
            line_spacing=3
        )

        self.cached_lines = [name_surf, pop_surf, stats_surf, desc_surf]

        total_height = sum(line.get_height() + 4 for line in self.cached_lines)
        max_line_width = max(line.get_width() for line in self.cached_lines)

        panel_w = min(self.max_width, max_line_width + int(self.margin_x * 2))
        panel_h = min(self.max_height, total_height + int(self.margin_y * 2) + 10)
        panel_h = max(100, panel_h)

        self.info_panel = pygame.transform.scale(self.info_panel_surface, (panel_w, panel_h))
        self.info_panel_rect = self.info_panel.get_rect(topright=(self.width - int(self.margin_x), int(self.margin_y)))
        self.cached_district = district_name

    def draw_panel(self):
        mouse_pos = pygame.mouse.get_pos()

        # 1. Render Back Button
        alpha = 180 if self.back_rect.collidepoint(mouse_pos) else 255
        self.back_button.set_alpha(alpha)
        self.screen.blit(self.back_button, self.back_rect)

        # 2. Check Selection State
        district_name = self.dl.selected_district
        if not district_name:
            self.cached_district = None
            return

        # Rebuild cache if selection changed
        if district_name != self.cached_district:
            self._rebuild_panel_cache(district_name)

        if self.info_panel is None or self.info_panel_rect is None:
            return

        # 3. Render Panel Surface & Text
        self.screen.blit(self.info_panel, self.info_panel_rect)

        # Extract explicit coordinates to prevent IDE type warnings
        top_y = int(self.info_panel_rect.top)
        center_x = int(self.info_panel_rect.centerx)

        start_y = top_y + int(self.margin_y) + 5
        for line_surf in self.cached_lines:
            line_rect = line_surf.get_rect(midtop=(center_x, start_y))
            self.screen.blit(line_surf, line_rect)
            start_y += line_surf.get_height() + 4

        # 4. Render Begin Button
        btn_alpha = 180 if self.button_rect.collidepoint(mouse_pos) else 255
        self.button.set_alpha(btn_alpha)
        self.screen.blit(self.button, self.button_rect)
        self.screen.blit(self.begin_text, self.begin_text_rect)

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.back_rect.collidepoint(event.pos):
                return "back"

            if self.dl.selected_district is not None and self.button_rect.collidepoint(event.pos):
                return "begin"

        return None
