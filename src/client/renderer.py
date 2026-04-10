import pygame
from common.constants import *

def draw(screen, state, net):
    screen.fill((0, 0, 0))

    pygame.draw.rect(screen, (255,255,255), (10, state["paddles"][0], PADDLE_WIDTH, PADDLE_HEIGHT))
    pygame.draw.rect(screen, (255,255,255), (WIDTH-20, state["paddles"][1], PADDLE_WIDTH, PADDLE_HEIGHT))

    pygame.draw.rect(screen, (255,255,255), (state["ball"]["x"], state["ball"]["y"], BALL_SIZE, BALL_SIZE))

    font = pygame.font.Font(None, 24)
    lat = font.render(f"Latency: {int(net.latency*1000)} ms", True, (255,255,255))
    jit = font.render(f"Jitter: {int(net.jitter*1000)} ms", True, (255,255,255))

    screen.blit(lat, (10, 10))
    screen.blit(jit, (10, 30))