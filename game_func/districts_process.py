import json
from shapely.geometry import Polygon, MultiPolygon, shape

class DistProc:
    # Processes GeoJSON geographic data and translates coordinates into
    # DataLoader's virtual canvas coordinate system.

    def __init__(self, data_loader_instance, geojson_path='data/bhutan_districts.geojson'):
        self.data_loader = data_loader_instance

        # Always lock bounds and scaling to virtual canvas resolution
        self.width = self.data_loader.VIRTUAL_WIDTH
        self.height = self.data_loader.VIRTUAL_HEIGHT

        # Load GeoJSON data
        try:
            with open(geojson_path, 'r', encoding='utf-8') as raw_data:
                geo_data = json.load(raw_data)
        except (FileNotFoundError, json.JSONDecodeError) as load_error:
            print(f"Error loading GeoJSON file at {geojson_path}: {load_error}")
            geo_data = {'features': []}

        self.features = geo_data.get('features', [])
        self.geometry = [shape(feature['geometry']) for feature in self.features if 'geometry' in feature]

        if not self.geometry:
            self.overall_minx = self.overall_miny = 0
            self.overall_maxx = self.overall_maxy = 1
        else:
            # Calculate overall spatial bounding box
            bounds = [geom.bounds for geom in self.geometry]
            self.overall_minx = min(b[0] for b in bounds)
            self.overall_miny = min(b[1] for b in bounds)
            self.overall_maxx = max(b[2] for b in bounds)
            self.overall_maxy = max(b[3] for b in bounds)

        # Apply spatial layout margins based on virtual screen size
        self.padding = int(0.02 * self.height)
        self.right_margin = int(self.width * 0.15)

        self.raw_width = self.overall_maxx - self.overall_minx
        self.raw_height = self.overall_maxy - self.overall_miny

        self.usable_width = self.width - self.padding - self.right_margin
        self.usable_height = self.height - (self.padding * 2)

        # Scale factor preserving geographic aspect ratio
        scale_x = self.usable_width / max(1e-6, self.raw_width)
        scale_y = self.usable_height / max(1e-6, self.raw_height)
        self.final_scale = min(scale_x, scale_y)

        # Center map on canvas (left‑aligned)
        self.x_offset = self.padding
        self.y_offset = (self.height - (self.raw_height * self.final_scale)) / 1.3

        self.pygame_coords = self._build_pygame_coords()
        self.districts = self._build_polygons()

    def conversion(self, raw_x, raw_y):
        # Translates raw longitude/latitude to Pygame virtual canvas coordinates.
        final_pygame_x = ((raw_x - self.overall_minx) * self.final_scale) + self.x_offset
        final_pygame_y = (self.height - (raw_y - self.overall_miny) * self.final_scale) - self.y_offset
        return int(round(final_pygame_x)), int(round(final_pygame_y))

    def _get_district_name(self, props):
        # Flexible property key fallback for district names.
        for key in ['shapeName']:
            if key in props:
                return props[key]
        return 'Unknown'

    def _build_pygame_coords(self):
        # Converts geographic shapes to lists of screen-space polygon points.
        result = []
        for feature, geom in zip(self.features, self.geometry):
            props = feature.get('properties', {})
            name = self._get_district_name(props)

            if isinstance(geom, Polygon):
                pygame_points = [self.conversion(x, y) for x, y in geom.exterior.coords]
                result.append({'name': name, 'coords': [pygame_points]})

            elif isinstance(geom, MultiPolygon):
                # Preserve all sub-polygons for complete district coverage
                all_parts = []
                for poly in geom.geoms:
                    pygame_points = [self.conversion(x, y) for x, y in poly.exterior.coords]
                    all_parts.append(pygame_points)
                result.append({'name': name, 'coords': all_parts})

        return result

    def _build_polygons(self):
        # Builds Shapely Polygons and MultiPolygons for point-in-polygon collision tests.
        districts = {}
        for district_data in self.pygame_coords:
            name = district_data['name']
            parts = district_data['coords']

            if len(parts) == 1:
                districts[name] = Polygon(parts[0])
            else:
                districts[name] = MultiPolygon([Polygon(p) for p in parts])

        return districts
