import json
import shapely.geometry as sg
from shapely.geometry import Polygon

class DistProc:
    def __init__(self, data_loader_instance):
        self.dl = data_loader_instance
        self.width = self.dl.WIDTH
        self.height = self.dl.HEIGHT

        with open('data/bhutan_districts.geojson', 'r') as raw_data:
            data = json.load(raw_data)

        self.geometry = [sg.shape(d['geometry']) for d in data['features']]

        self.minx_list = [shape.bounds[0] for shape in self.geometry]
        self.miny_list = [shape.bounds[1] for shape in self.geometry]
        self.maxx_list = [shape.bounds[2] for shape in self.geometry]
        self.maxy_list = [shape.bounds[3] for shape in self.geometry]
        self.overall_minx = min(self.minx_list)
        self.overall_miny = min(self.miny_list)
        self.overall_maxx = max(self.maxx_list)
        self.overall_maxy = max(self.maxy_list)
        self.padding = 50
        self.final_x = self.overall_maxx - self.overall_minx
        self.final_y = self.overall_maxy - self.overall_miny

        self.usable_width = self.width - (self.padding*2)
        self.usable_height = self.height - (self.padding*2)

        self.scaleX = self.usable_width/self.final_x
        self.scaleY = self.usable_height/self.final_y

        self.final_scale = min(self.scaleX, self.scaleY)

        self.x_offset = ((self.width - (self.final_x * self.final_scale)) / 2)
        self.y_offset = ((self.height - (self.final_y * self.final_scale)) / 2)

    def conversion(self, raw_x, raw_y):
        final_pygame_x= ((raw_x - self.overall_minx) * self.final_scale) + self.x_offset
        final_pygame_y = (self.height - (raw_y - self.overall_miny) * self.final_scale) - self.y_offset
        return int(round(final_pygame_x + 0.5)), int(round(final_pygame_y + 0.5))

    def poly_maker(self):
        with open('data/pygame_coordinates.json', 'r') as file:
            data = json.load(file)

        self.districts = {}

        for values in data:
            coords = values['coords']
            name = values['name']
            poly = Polygon(coords)
            self.districts[name] = poly
