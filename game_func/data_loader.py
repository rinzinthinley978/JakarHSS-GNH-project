import pygame

pygame.mixer.init()
class DataLoader:
    def __init__(self):
        self.bg_music = pygame.mixer.music.load("assets/sounds/background/M1.wav")
        self.main_menu = pygame.image.load('assets/ui/main_menu.png')
        self.game_icon = pygame.image.load("assets/ui/icon.png")
        info = pygame.display.Info()
        self.WIDTH = info.current_w
        self.HEIGHT = info.current_h
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.RESIZABLE)
        self.title = "GNH"
        self.selected_district = None
        self.hovered = None
        self.mousePos = pygame.mouse.get_pos()
