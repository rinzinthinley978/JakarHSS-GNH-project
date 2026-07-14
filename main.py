import sys
import os
import time
import pygame
from game_func.district_loader import MapScreen
from game_func.loading import loadingScreen
from game_func.data_loader import DataLoader
from game_func.districts_process import DistProc

time.sleep(0.5)
pygame.init()
pygame.mixer.init()

dl = DataLoader()
proc = DistProc(dl)
loader = loadingScreen(dl)

if os.path.exists('data/pygame_coordinates.json'):
    print("Coordinates checked!, Loading...")
else:
    from game_func.json_convertor import Convertor
    print("⚠️  Coordinates missing! Generating now...")
    print("    Processing GeoJSON data...")
    js_conv = Convertor(dl, proc)
    js_conv.convertJson()
    print("    Conversion complete! File saved.")

map = MapScreen(dl,proc)

pygame.mixer.music.play(-1)
pygame.mixer.music.set_volume(0.5)

pygame.display.set_icon(dl.game_icon)
pygame.display.set_caption(dl.title)

running = True
last_mousePos = None

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
                print("selected", dl.selected_district)
    if not loader.loading_finsished:
        loader.check_loading()
    else:
        dl.screen.fill('#474427')
        map.draw(dl.screen)
    pygame.display.flip()
pygame.quit()
sys.exit()
