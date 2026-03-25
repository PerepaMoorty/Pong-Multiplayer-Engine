import pygame
from common.constants import *

def draw(screen, state):
    screen.fill((0, 0, 0))

    pygame.draw.rect(screen, (255,255,255), (10, state["paddles"][0], PADDLE_WIDTH, PADDLE_HEIGHT))
    pygame.draw.rect(screen, (255,255,255), (WIDTH-20, state["paddles"][1], PADDLE_WIDTH, PADDLE_HEIGHT))

    pygame.draw.rect(screen, (255,255,255), (state["ball"]["x"], state["ball"]["y"], BALL_SIZE, BALL_SIZE))

    pygame.display.flip()