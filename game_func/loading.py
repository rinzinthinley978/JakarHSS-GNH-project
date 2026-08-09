import pygame

class loadingScreen:
    def __init__(self, data_loader_instance, font_manager_instance):
        self.data_loader = data_loader_instance
        self.font = font_manager_instance
        self.screen = self.data_loader.screen
        self.width, self.height = self.data_loader.WIDTH, self.data_loader.HEIGHT
        self.loading_text = self.font.Font('LOADING . . .', "#4AA611", 60)

        self.work = 1000
        self.target_duration_ms = 3000
        self.loading_finished = False
        self.loading_progress = 0

        # Pre-calculated max bar dimensions
        self.max_bar_width = int(self.width * 0.56)
        self.bar_height = int(self.height * 0.2)

        try:
            raw_progress = pygame.image.load("assets/ui/loading_bar_progress.png").convert_alpha()
            raw_layout = pygame.image.load("assets/ui/loading_bar_layout.png").convert_alpha()
            raw_icon = pygame.image.load("assets/ui/icon.png").convert_alpha()

            self.loading_bar_progress = pygame.transform.scale(
                raw_progress, (self.max_bar_width, self.bar_height)
            )
            self.loading_bar_layout = pygame.transform.scale(
                raw_layout, (int(self.width * 0.59), int(self.height * 0.2))
            )
            self.scaled_icon = pygame.transform.scale(raw_icon, (370, 370))

        except (FileNotFoundError, pygame.error) as load_error:
            print(f"Warning: Loading screen assets missing ({load_error}). Using fallbacks.")

            # Fallback surfaces
            self.loading_bar_layout = pygame.Surface((int(self.width * 0.59), int(self.height * 0.2)))
            self.loading_bar_layout.fill((40, 40, 40))

            self.loading_bar_progress = pygame.Surface((self.max_bar_width, self.bar_height))
            self.loading_bar_progress.fill((74, 166, 17))

            self.scaled_icon = pygame.Surface((370, 370))
            self.scaled_icon.fill((100, 100, 100))

        # Positioning Rects
        self.loading_bar_layout_rect = self.loading_bar_layout.get_rect(
            center=(self.width // 2, int(self.height * 0.723))
        )
        self.loading_bar_progress_rect = self.loading_bar_progress.get_rect(
            midleft=(int(self.width * 0.22), self.loading_bar_layout_rect.centery)
        )
        self.gameIcon_rect = self.scaled_icon.get_rect(
            center=(self.width // 2, int(self.height * 0.347))
        )
        self.loading_rect = self.loading_text.get_rect(
            center=(self.width // 2, int(self.height * 0.9))
        )

    def do_work(self, delta_time):
        # Updates loading progress based on elapsed delta time.
        if self.loading_finished:
            return

        self.loading_progress += (delta_time / self.target_duration_ms) * self.work
        if self.loading_progress >= self.work:
            self.loading_progress = self.work
            self.loading_finished = True

    def check_loading(self):
        # Renders the loading screen assets using clip rects to avoid runtime image scaling.
        if self.loading_finished:
            return

        ratio = self.loading_progress / float(self.work)
        current_width = int(self.max_bar_width * ratio)

        # Draw Base Elements
        self.screen.blit(self.loading_bar_layout, self.loading_bar_layout_rect)
        self.screen.blit(self.scaled_icon, self.gameIcon_rect)
        self.screen.blit(self.loading_text, self.loading_rect)

        # Draw progress using blit area masking (no scaling overhead)
        if current_width > 0:
            clip_area = pygame.Rect(0, 0, current_width, self.bar_height)
            self.screen.blit(self.loading_bar_progress, self.loading_bar_progress_rect, area=clip_area)
