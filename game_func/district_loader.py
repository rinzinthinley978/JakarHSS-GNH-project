import json
import pygame
from shapely.geometry import Point

class MapScreen:
    def __init__(self, data_loader_instance, DistProc_instance):
        self.dl = data_loader_instance
        self.proc = DistProc_instance
        with open('data/pygame_coordinates.json', 'r') as file:
            coords = json.load(file)
        self.final_coords = coords
        self.proc.poly_maker()

    def draw(self, surface):
        for district_obj in self.final_coords:
            name = district_obj['name']
            points = district_obj['coords']

            if name == self.dl.selected_district:
                color, width = '#ff0000', 10
            elif name == self.dl.hovered:
                color, width = '#0066ff', 10
            else:
                color, width = '#00ff00', 10  # Green instead of black

            pygame.draw.polygon(surface, color, points, width=width)


    def check_hover(self):
        self.dl.hovered = None
        for district in self.proc.districts:
            polygon = self.proc.districts[district]
            if polygon.contains(Point(self.dl.mousePos)):
                self.dl.hovered = district
                break

    def check_click(self):
        self.dl.selected_district = self.dl.hovered
