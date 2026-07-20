import pygame

class FontManager:
    def __init__(self, font_path='assets/ui/pixel_font.ttf'):
        self.font_path = font_path

    def Font(self, text, color, size):
        font = pygame.font.Font(self.font_path, size)
        font_render = font.render(text, True, color)
        return font_render
