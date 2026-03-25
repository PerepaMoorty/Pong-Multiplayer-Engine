import pygame
from client.network import Network
from client.input_handler import get_input
from client.renderer import draw
from common.constants import *

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

net = Network("127.0.0.1", 5555)

game_started = False
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
    if data:
        if data["type"] == "START":
            game_started = True

        elif data["type"] == "RESET":
            state = data

        elif data["type"] == "STATE" and game_started:
            state = data

    if game_started and state:
        draw(screen, state)