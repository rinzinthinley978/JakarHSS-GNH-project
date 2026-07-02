import sys

import pygame
import pygame_menu


class LoadingScreen:
    def __init__(self, surface, width, height):
        self.surface = surface
        self.width = width
        self.height = height
        self.clock = pygame.time.Clock()
        self.loading_complete = False

        # Custom Event ID
        self.LOADING_EVENT = pygame.USEREVENT + 1

        # Create Loading Menu
        self.menu = pygame_menu.Menu(
            "Loading", width, height, theme=pygame_menu.themes.THEME_DARK
        )
        self.status_label = self.menu.add.label("Initializing...", label_id="status")
        self.progress_bar = self.menu.add.progress_bar(
            "Progress: ", progressbar_id="1", default=0, width=300
        )

    def _update_progress(self):
        """Increment progress bar and check completion."""
        current_val = self.progress_bar.get_value()
        if current_val < 100:
            new_val = current_val + 1
            self.progress_bar.set_value(new_val)

            # Update text status
            if new_val < 30:
                self.status_label.set_title("Loading assets...")
            elif new_val < 70:
                self.status_label.set_title("Processing data...")
            else:
                self.status_label.set_title("Finalizing...")
        else:
            self.loading_complete = True
            pygame.time.set_timer(self.LOADING_EVENT, 0)  # Stop timer

    def run(self):
        """
        Runs the loading loop.
        Returns True if loading completes, False if user quits.
        """
        # Start timer (updates every 50ms)
        pygame.time.set_timer(self.LOADING_EVENT, 50)

        running = True
        while running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    return False  # User quit

                if event.type == self.LOADING_EVENT and not self.loading_complete:
                    self._update_progress()

            # Draw
            self.surface.fill((30, 30, 30))  # Dark background

            if not self.loading_complete:
                self.menu.update(events)
                self.menu.draw(self.surface)
            else:
                running = False  # Exit loop when 100%

            pygame.display.flip()
            self.clock.tick(60)

        return True  # Success
