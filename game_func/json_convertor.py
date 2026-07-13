# game_func/json_convertor.py
import json
import geojson
import shapely.geometry as sg
from shapely.geometry import MultiPolygon, Polygon

class Convertor:
    def __init__(self, data_loader_instance, DistProc_instance):  # 1. Accept the instance
        self.dl = data_loader_instance
        # Use the screen from the passed instance
        self.proc = DistProc_instance

        with open('data/bhutan_districts.geojson', 'r') as raw_data:
            data = geojson.load(raw_data)

        self.district_data = data['features']
        self.processed = []

        for district in self.district_data:
            coords = []
            name = district['properties'].get('shapeName', 'Unknown') # Use .get() to be safe
            shape = sg.shape(district['geometry'])

            if isinstance(shape, Polygon):
                coords.extend(list(shape.exterior.coords))
            elif isinstance(shape, MultiPolygon):
                for poly in shape.geoms:
                    coords.extend(list(poly.exterior.coords))

            self.processed.append({
                "name": name,
                "coords": coords
            })

    def convertJson(self):
        with open('data/coordinates.json', 'w') as file:
            json.dump(self.processed, file, indent=4)

        final_data = []
        # FIX: Loop through 'self.processed' (list of dicts), not directly over x,y
        for entry in self.processed:
            points = entry['coords']
            # Convert every point in this district
            converted_points = [list(self.proc.conversion(x, y)) for x, y in points]
            self.final_entry = {
                "name" : entry['name'],
                "coords" : converted_points
            }
            final_data.append(self.final_entry)


        with open('data/pygame_coordinates.json', 'w') as file:
            json.dump(final_data, file, indent=4)
