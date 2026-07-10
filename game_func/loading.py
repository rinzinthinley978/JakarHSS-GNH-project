import pygame


class loadingScreen:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.work = 100000000
        self.loading_font = pygame.font.SysFont("Times New Roman", 50)
        self.loading = self.loading_font.render("Loading . . .", True, (10, 255, 10))

        try:
            self.loading_bar_progress = pygame.image.load(
                "assets/ui/loading_bar_progress.png"
            ).convert_alpha()
            self.loading_bar_layout = pygame.image.load(
                "assets/ui/loading_bar_layout.png"
            ).convert_alpha()
            self.gameIcon = pygame.image.load("assets/ui/icon.png").convert_alpha()
        except FileNotFoundError:
            print("File missing, pleasse recheck the files")

        self.loading_bar_layout_rect = self.loading_bar_layout.get_rect(
            center=(640, 525)
        )
        self.loading_bar_progress_rect = self.loading_bar_progress.get_rect(
            midleft=(280, 533)
        )

        self.scaledIcon = pygame.transform.smoothscale(self.gameIcon, (370, 370))
        self.gameIcon_rect = self.scaledIcon.get_rect(center=(640, 250))
        self.loading_rect = self.loading.get_rect(center=(640, 650))

        self.loading_finsished = False
        self.loading_progress = 0
        self.loading_bar_width = 8

    def do_work(self):
        for i in range(self.work):
            self.loading_progress = i
        self.loading_finsished = True

    def check_loading(self):
        if not self.loading_finsished:
            ratio = float(self.loading_progress) / float(self.work)

            self.loading_bar_width = int(ratio * 720)

            self.loading_bar_progress = pygame.transform.scale(self.loading_bar_progress, (int(self.loading_bar_width), 150))

            self.screen.blit(self.loading_bar_layout, self.loading_bar_layout_rect)
            self.screen.blit(self.loading_bar_progress, self.loading_bar_progress_rect)
            self.screen.blit(self.scaledIcon, self.gameIcon_rect)
            self.screen.blit(self.loading, self.loading_rect)
