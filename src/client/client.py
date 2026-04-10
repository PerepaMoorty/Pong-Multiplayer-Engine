import pygame
import time
from client.network import Network
from client.input_handler import get_input
from client.renderer import draw
from common.constants import *

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Multiplayer Pong")

clock = pygame.time.Clock()

server_ip = input("Enter server IP address: ")
net = Network(server_ip, 5555)

game_started = False
state = None

last_ping = 0

while True:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    # heartbeat
    if time.time() - last_ping > 0.5:
        net.heartbeat()
        last_ping = time.time()

    move = get_input()

    if move:
        net.send({"type": "INPUT", "move": move})

        if state:
            if move == "UP":
                state["paddles"][0] -= PADDLE_SPEED
            elif move == "DOWN":
                state["paddles"][0] += PADDLE_SPEED

    data = net.receive()

    if data:
        if data["type"] == "START":
            game_started = True

        elif data["type"] == "RESET":
            state = data
            net.pending_inputs.clear()

        elif data["type"] == "STATE" and game_started:
            state = data

            for inp in net.pending_inputs:
                if inp["move"] == "UP":
                    state["paddles"][0] -= PADDLE_SPEED
                elif inp["move"] == "DOWN":
                    state["paddles"][0] += PADDLE_SPEED

    if game_started and state:
        draw(screen, state, net)
    else:
        screen.fill((0, 0, 0))
        font = pygame.font.Font(None, 36)
        text = font.render("Waiting for game to start...", True, (255, 255, 255))
        screen.blit(text, (WIDTH//4, HEIGHT//2))

    pygame.display.update()