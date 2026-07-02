# importing the required libraries
import sys  # for system-level operations

import pygame as pg  # for game development

# initializing pygame
pg.init()


# assigning required variables to control the flow of the game
# assigning the variables related to the display
title = "Gross National Happiness Simulator"
game_icon = pg.image.load("logo.png")
screen = pg.display.set_mode((0, 0), pg.FULLSCREEN)

# assigning the variables related to the game loop
running = True
clock = pg.time.Clock()

# assigning the game icon and caption/title
pg.display.set_icon(game_icon)
pg.display.set_caption(title)


# main game loop
while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

    # updating the display and ticking the clock
    pg.display.flip()
    clock.tick(60)

# quitting pygame
pg.quit()
sys.exit()
