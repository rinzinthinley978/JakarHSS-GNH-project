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
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT),pygame.FULLSCREEN,pygame.RESIZABLE)
        self.title = "GNH"
        self.selected_district = None
        self.hovered = None
        self.mousePos = pygame.mouse.get_pos()
        self.frames = 60
        self.clock = pygame.time.Clock()
        orig_mouse_sprite = pygame.image.load('assets/ui/mouse_icon.png').convert_alpha()
        mouse_sprite = pygame.transform.scale(orig_mouse_sprite, (32,32))
        self.cursor_sprite = pygame.cursors.Cursor((0,0), mouse_sprite)

    def show_fps(self, enabled):
        enabled = bool(enabled)
        if not enabled:
            return
        font = pygame.font.SysFont("Arial", 50)
        fps = str(int(self.clock.get_fps()))
        fps_ren = font.render(fps, True, (255, 0, 0))
        self.screen.blit(fps_ren, (10,10))
