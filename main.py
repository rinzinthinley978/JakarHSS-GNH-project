import sys
import threading
import time

import pygame

from game_func.loading import loadingScreen

time.sleep(0.5)
pygame.init()
pygame.mixer.init()

pygame.mixer.music.load("assets/sounds/background/M1.wav")
pygame.mixer.music.play(-1)
pygame.mixer.music.set_volume(0.5)

WIDTH = 1280
HEIGHT = 720
game_icon = pygame.image.load("assets/ui/icon.png")
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
title = "GNH"
clock = pygame.time.Clock()
running = True
frames = 60

loader = loadingScreen(screen)
threading.Thread(target=loader.do_work).start()

pygame.display.set_icon(game_icon)
pygame.display.set_caption(title)

while running:
    screen.fill("#0b0e2e")
    loader.check_loading()
    for event in pygame.event.get():
        if event == pygame.QUIT:
            running = False
    pygame.display.flip()
    clock.tick(frames)
pygame.quit()
sys.exit()
