import pygame

class Panel:
    def __init__(self, data_loader_instance, font_manager_instance):
        self.dl = data_loader_instance
        self.font = font_manager_instance
        self.screen = self.dl.screen
        self.padding = 10

        try:
            self.panel = pygame.image.load('assets/ui/selection_box.png').convert_alpha()
        except:
            print("Panel's asset is missing")


    def draw_panel(self):
        self.text = self.font.Font(self.dl.selected_district,(255,255,255), 40)
        scaleX = ((self.padding * 2) + self.text.get_width())//self.panel.get_width()
        scaleY = ((self.padding * 2) + self.text.get_height())//self.panel.get_height()
        panel = pygame.transform.scale(self.panel, (scaleX*100, scaleY*100))
        self.dl.screen.blit(panel, (0,0))
