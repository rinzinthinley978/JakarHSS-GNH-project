import pygame

class loadingScreen:
    # This class handles the loading screen display and progress animation.
    def __init__(self, data_loader_instance, font_manager_instance):
        # Store references to the data loader (for screen and dimensions) and font manager.
        self.data_loader = data_loader_instance
        self.font = font_manager_instance

        # Draw on the virtual surface (used for scaling) rather than directly on the real screen.
        self.screen = self.data_loader.virtual_surface
        self.width, self.height = self.data_loader.VIRTUAL_WIDTH, self.data_loader.VIRTUAL_HEIGHT

        # Create the "LOADING..." text surface with custom font.
        self.loading_text = self.font.Font('LOADING . . .', "#4AA611", 60)

        # Total work units for the progress bar (used to track completion).
        self.work = 1000
        # Target time (in milliseconds) for the loading animation to finish.
        self.target_duration_ms = 3000
        # Flag indicating whether loading has completed.
        self.loading_finished = False
        # Current progress value (in work units).
        self.loading_progress = 0

        # Dimensions for the loading bar.
        self.max_bar_width = int(self.width * 0.56)      # Maximum width of the filled progress bar.
        self.bar_height = int(self.height * 0.2)         # Height of the bar.

        try:
            # Attempt to load custom loading screen assets (progress bar, layout, and icon).
            raw_progress = pygame.image.load("assets/ui/loading_bar_progress.png").convert_alpha()
            raw_layout = pygame.image.load("assets/ui/loading_bar_layout.png").convert_alpha()
            raw_icon = pygame.image.load("assets/ui/icon.png").convert_alpha()

            # Scale the loaded images to the required dimensions.
            self.loading_bar_progress = pygame.transform.scale(
                raw_progress, (self.max_bar_width, self.bar_height)
            )
            self.loading_bar_layout = pygame.transform.scale(
                raw_layout, (int(self.width * 0.59), int(self.height * 0.2))
            )
            self.scaled_icon = pygame.transform.scale(raw_icon, (370, 370))

        except (FileNotFoundError, pygame.error) as load_error:
            # If assets are missing, print a warning and create fallback surfaces.
            print(f"Warning: Loading screen assets missing ({load_error}). Using fallbacks.")
            # Fallback layout surface (dark gray).
            self.loading_bar_layout = pygame.Surface((int(self.width * 0.59), int(self.height * 0.2)))
            self.loading_bar_layout.fill((40, 40, 40))
            # Fallback progress bar surface (green).
            self.loading_bar_progress = pygame.Surface((self.max_bar_width, self.bar_height))
            self.loading_bar_progress.fill((74, 166, 17))
            # Fallback icon surface (light gray).
            self.scaled_icon = pygame.Surface((370, 370))
            self.scaled_icon.fill((100, 100, 100))

        # Position the layout bar at the bottom third of the screen.
        self.loading_bar_layout_rect = self.loading_bar_layout.get_rect(
            center=(self.width // 2, int(self.height * 0.723))
        )
        # Position the progress bar's left edge aligned with the layout bar.
        self.loading_bar_progress_rect = self.loading_bar_progress.get_rect(
            midleft=(int(self.width * 0.22), self.loading_bar_layout_rect.centery)
        )
        # Position the icon near the top center.
        self.gameIcon_rect = self.scaled_icon.get_rect(
            center=(self.width // 2, int(self.height * 0.347))
        )
        # Position the loading text below the bar.
        self.loading_rect = self.loading_text.get_rect(
            center=(self.width // 2, int(self.height * 0.9))
        )

    def do_work(self, delta_time):
        # Update the loading progress based on elapsed time.
        # If loading is already finished, do nothing.
        if self.loading_finished:
            return
        # Increase progress proportionally to the time passed relative to target duration.
        self.loading_progress += (delta_time / self.target_duration_ms) * self.work
        # If progress reaches or exceeds the total work, clamp it and mark as finished.
        if self.loading_progress >= self.work:
            self.loading_progress = self.work
            self.loading_finished = True

    def check_loading(self):
        # Draw the loading screen elements each frame.
        # If loading is finished, skip drawing.
        if self.loading_finished:
            return

        # Calculate the current width of the progress bar based on completion ratio.
        ratio = self.loading_progress / float(self.work)
        current_width = int(self.max_bar_width * ratio)

        # Draw the static layout bar, icon, and loading text onto the virtual surface.
        self.screen.blit(self.loading_bar_layout, self.loading_bar_layout_rect)
        self.screen.blit(self.scaled_icon, self.gameIcon_rect)
        self.screen.blit(self.loading_text, self.loading_rect)

        # Draw the progress fill only if its width is positive.
        if current_width > 0:
            # Create a clipping area to show only the left part of the progress image.
            clip_area = pygame.Rect(0, 0, current_width, self.bar_height)
            # Blit the progress bar with the clip area.
            self.screen.blit(self.loading_bar_progress, self.loading_bar_progress_rect, area=clip_area)
