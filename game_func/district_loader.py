import json
import pygame
from shapely.geometry import Point


class MapScreen:
    def __init__(self, data_loader_instance, DistProc_instance, font_manager_instance):
        self.dl = data_loader_instance
        self.proc = DistProc_instance
        self.font = font_manager_instance
        with open('data/pygame_coordinates.json', 'r') as file:
            coords = json.load(file)
        self.final_coords = coords
        self.proc.poly_maker()
        self.dl.hovered = None
        self.in_boundary = False
        self.text = self.font.Font("----SELECT A DISTRICT----", '#82A118', 60)
        self.text_rect = self.text.get_rect(center=(self.dl.WIDTH//2, int(0.92448*self.dl.HEIGHT)))

    def draw(self, surface):
        for district_obj in self.final_coords:
            name = district_obj['name']
            points = district_obj['coords']

            pygame.draw.polygon(surface, '#3C9134', points)
            pygame.draw.polygon(surface, '#000000', points, width=2)
            if name == self.dl.selected_district:
                color, width = '#FF0000', 6
                pygame.draw.polygon(surface, color, points, width=width)
            elif name == self.dl.hovered:
                color, width = '#151D60', 6
                pygame.draw.polygon(surface, color, points, width=width)

            self.dl.screen.blit(self.text, self.text_rect)


    def check_hover(self):
        for district in self.proc.districts:
            self.polygon = self.proc.districts[district]
            if self.polygon.contains(Point(self.dl.mousePos)):
                self.dl.hovered = district
                break
            else:
                self.dl.hovered = None

    def check_click(self):
        self.dl.selected_district = self.dl.hovered
