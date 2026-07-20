import sys
import os
import time
import pygame
from game_func.district_loader import MapScreen
from game_func.loading import loadingScreen
from game_func.data_loader import DataLoader
from game_func.districts_process import DistProc
from game_func.ui_panel import Panel
from game_func.font_manager import FontManager

pygame.init()
pygame.mixer.init()
dl = DataLoader()
proc = DistProc(dl)
font = FontManager()
loader = loadingScreen(dl, font)
panel = Panel(dl, font)

if os.path.exists('data/pygame_coordinates.json'):
    print("Coordinates checked!, Loading...")
else:
    from game_func.json_convertor import Convertor
    print("⚠️  Coordinates missing! Generating now...")
    print("    Processing GeoJSON lf.text = self.font.Font()data...")
    js_conv = Convertor(dl, proc)
    js_conv.convertJson()
    print("    Conversion complete! File saved.")

map = MapScreen(dl, proc, font)

pygame.mixer.music.play(-1)
pygame.mixer.music.set_volume(0.5)

pygame.display.set_icon(dl.game_icon)
pygame.display.set_caption(dl.title)

running = True
last_mousePos = None

pygame.mouse.set_cursor(dl.cursor_sprite)
time.sleep(0.5)
while running:
    dl.mousePos = pygame.mouse.get_pos()
    dl.screen.fill('#fff0f1')
    dt = dl.clock.tick(dl.frames)
    loader.do_work(dt)
    dl.show_fps(0)
    if dl.mousePos != last_mousePos:
        map.check_hover()
        last_mousePos = dl.mousePos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                map.check_click()
    if dl.selected_district != None:
        panel.draw_panel()

    if not loader.loading_finsished:
        loader.check_loading()
    else:
        map.draw(dl.screen)
    pygame.display.flip()
pygame.quit()
sys.exit()
