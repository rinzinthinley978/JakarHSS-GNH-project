import pygame

class loadingScreen:
    def __init__(self, data_loader_instanace):
        self.dl = data_loader_instanace
        self.screen = self.dl.screen
        self.width, self.height = self.dl.WIDTH, self.dl.HEIGHT
        self.work = 100000000
        self.loading_font = pygame.font.SysFont("Times New Roman", 50)
        self.loading = self.loading_font.render("Loading . . .", True, (10, 255, 10))

        try:
            self.loading_bar_progress = pygame.image.load(
                "assets/ui/loading_bar_progress.png"
            ).convert_alpha()
            self.loading_bar_progress = pygame.transform.scale(self.loading_bar_progress, (int(self.width*0.00625), int(self.height*0.23)))
            self.loading_bar_layout = pygame.image.load(
                "assets/ui/loading_bar_layout.png"
            ).convert_alpha()
            self.loading_bar_layout = pygame.transform.scale(self.loading_bar_layout, (int(self.width*0.59), int(self.height*0.2)))
            self.gameIcon = pygame.image.load("assets/ui/icon.png").convert_alpha()
        except FileNotFoundError:
            print("File missing, pleasse recheck the files")

        self.loading_bar_layout_rect = self.loading_bar_layout.get_rect(
            center=(self.width//2 , int(self.height*0.723))
        )
        self.loading_bar_progress_rect = self.loading_bar_progress.get_rect(
            midleft=(int(self.width*0.22), int(self.height * 0.74))
        )

        self.scaledIcon = pygame.transform.scale(self.gameIcon, (370, 370))
        self.gameIcon_rect = self.scaledIcon.get_rect(center=(self.width//2, int(self.height*0.347)))
        self.loading_rect = self.loading.get_rect(center=(self.width//2, int(self.height*0.9)))

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

            self.loading_bar_width = int(ratio * 2)

            self.loading_bar_progress = pygame.transform.scale(self.loading_bar_progress, (int(self.loading_bar_width), 150))

            self.screen.blit(self.loading_bar_layout, self.loading_bar_layout_rect)
            self.screen.blit(self.loading_bar_progress, self.loading_bar_progress_rect)
            self.screen.blit(self.scaledIcon, self.gameIcon_rect)
            self.screen.blit(self.loading , self.loading_rect)
