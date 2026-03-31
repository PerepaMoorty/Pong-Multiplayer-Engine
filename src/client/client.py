import pygame
from client.network import Network
from client.input_handler import get_input
from client.renderer import draw
from common.constants import *

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Multiplayer Pong")

clock = pygame.time.Clock()

# take server IP from user instead of hardcoding
server_ip = input("Enter server IP: ")
net = Network(server_ip, 5555)

game_started = False
state = None

while True:
    clock.tick(FPS)

    # handle window close
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    # get player input
    move = get_input()
    if move:
        net.send({
            "type": "INPUT",
            "move": move
        })

    # receive data from server
    data = net.receive()

    if data:
        if data["type"] == "START":
            game_started = True
            print("Game started!")

        elif data["type"] == "RESET":
            state = data

        elif data["type"] == "STATE" and game_started:
            state = data

    # draw game if started
    if game_started and state:
        draw(screen, state)
    else:
        # simple waiting screen
        screen.fill((0, 0, 0))
        font = pygame.font.Font(None, 36)
        text = font.render("Waiting for game to start...", True, (255, 255, 255))
        screen.blit(text, (WIDTH//4, HEIGHT//2))

    pygame.display.update()
