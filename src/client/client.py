import pygame
from network import Network
from input_handler import get_input
from renderer import draw
from common.constants import *

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

net = Network("127.0.0.1", 5555)

state = None

while True:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    move = get_input()
    if move:
        net.send({"type": "INPUT", "move": move})

    data = net.receive()
    if data and data["type"] == "STATE":
        state = data

    if state:
        draw(screen, state)