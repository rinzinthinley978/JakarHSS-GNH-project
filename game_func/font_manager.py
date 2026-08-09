import pygame

class FontManager:
    def __init__(self, font_path):
        self.font_path = font_path
        self._font_cache = {}

    def _get_font(self, size):
        # Retrieves cached font instance or instantiates a new one if missing.
        if size not in self._font_cache:
            try:
                self._font_cache[size] = pygame.font.Font(self.font_path, size)
            except Exception as load_error:
                print(f"Error loading font '{self.font_path}' at size {size}: {load_error}")
                self._font_cache[size] = pygame.font.SysFont("Arial", size)
        return self._font_cache[size]

    def Font(self, text, color, size):
        # Renders text string to a Pygame Surface without antialiasing.
        font = self._get_font(size)
        return font.render(str(text), False, color)

    def wrap_text(self, text, color, size, max_width, line_spacing=5, align="center"):
        # Wraps text across multiple lines and returns rendered surface.
        font = self._get_font(size)
        words = str(text).split(' ')
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.strip())

        if not lines:
            return pygame.Surface((max_width, 1), pygame.SRCALPHA)

        line_height = font.get_height()
        total_height = (len(lines) * line_height) + ((len(lines) - 1) * line_spacing)
        text_surface = pygame.Surface((max_width, max(1, total_height)), pygame.SRCALPHA)

        start_y = 0
        for line in lines:
            line_surf = font.render(line, False, color)

            # Support alignment options (center, left, right)
            if align == "left":
                line_rect = line_surf.get_rect(topleft=(0, start_y))
            elif align == "right":
                line_rect = line_surf.get_rect(topright=(max_width, start_y))
            else:   # Default center
                line_rect = line_surf.get_rect(centerx=max_width // 2, y=start_y)

            text_surface.blit(line_surf, line_rect)
            start_y += line_height + line_spacing

        return text_surface
