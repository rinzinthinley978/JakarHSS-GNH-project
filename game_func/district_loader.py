import pygame
from shapely.geometry import Point

class MapScreen:
    def __init__(self, data_loader_instance, DistProc_instance, font_manager_instance):
        self.dl = data_loader_instance
        self.proc = DistProc_instance
        self.font = font_manager_instance

        self.dl.hovered = None
        self.in_boundary = False

        self.text = self.font.Font("----SELECT A DISTRICT----", '#82A118', int(0.0651 * self.dl.HEIGHT))
        self.text_rect = self.text.get_rect(center=(self.dl.VIRTUAL_WIDTH // 2, int(0.92448 * self.dl.VIRTUAL_HEIGHT)))

        # Cache optimized district structures (including Shapely bounds)
        self.district_cache = []
        for district_obj in self.proc.pygame_coords:
            name = district_obj['name']
            parts = district_obj['coords']   # List of coordinate lists for MultiPolygons / Polygons
            polygon = self.proc.districts.get(name)

            # Pre-extract bounding boxes: (minx, miny, maxx, maxy)
            bounds = polygon.bounds if polygon else None

            self.district_cache.append({
                'name': name,
                'parts': parts,
                'polygon': polygon,
                'bounds': bounds
            })

    def draw(self, surface):
        # Renders district polygons with dynamic highlight borders in a single optimized pass.
        for district in self.district_cache:
            name = district['name']
            parts = district['parts']

            # Determine dynamic border styles
            if name == self.dl.selected_district:
                border_color = '#FF0000'
                border_width = 6
            elif name == self.dl.hovered:
                border_color = '#151D60'
                border_width = 6
            else:
                border_color = '#000000'
                border_width = 2

            # Iterate through each sub-polygon part (handles both single and MultiPolygons safely)
            for poly_points in parts:
                if poly_points and len(poly_points) >= 3:
                    # Base Fill
                    pygame.draw.polygon(surface, '#3C9134', poly_points)
                    # Border Pass
                    pygame.draw.polygon(surface, border_color, poly_points, width=border_width)

        surface.blit(self.text, self.text_rect)

    def check_hover(self):
        # Checks mouse position against districts using bounding box pruning before spatial queries.
        mouse_x, mouse_y = self.dl.mousePos
        self.dl.hovered = None

        for district in self.district_cache:
            polygon = district['polygon']
            bounds = district['bounds']

            if not polygon or not bounds:
                continue

            # Step 1: Bounding Box Pruning
            minx, miny, maxx, maxy = bounds
            if not (minx <= mouse_x <= maxx and miny <= mouse_y <= maxy):
                continue

            # Step 2: Accurate Point-in-Polygon check (only run if within bounding box)
            if polygon.contains(Point(mouse_x, mouse_y)):
                self.dl.hovered = district['name']
                break

    def check_click(self):
        # Handles selection toggling when clicking districts or empty spaces.
        if self.dl.hovered == self.dl.selected_district or self.dl.hovered is None:
            self.dl.selected_district = None
        else:
            self.dl.selected_district = self.dl.hovered
