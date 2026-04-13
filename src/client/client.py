"""
Multiplayer Pong — Client
==========================
1. Connects to server over TLS (JOIN → WELCOME) to get player_id + token.
2. Registers UDP address with the server using that token.
3. Enters the game loop: reads input, sends INPUT over UDP, applies
   client-side prediction, then reconciles when a server STATE arrives.
4. On RESET (point scored): clears prediction buffer and snaps to server state.
"""

import sys
import os
import pygame
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from client.network import Network
from client.input_handler import get_input
from client.renderer import draw
from common.constants import WIDTH, HEIGHT, FPS, PADDLE_SPEED


def main():
    server_ip = input("Server IP address: ").strip() or "127.0.0.1"

    print(f"[CLIENT] Connecting to {server_ip} …")
    try:
        net = Network(server_ip)
    except Exception as e:
        print(f"[CLIENT] Could not connect: {e}")
        sys.exit(1)

    player_id = net.player_id

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(f"Pong – Player {player_id + 1}")
    clock  = pygame.font.Font(None, 36)   # reused below
    ticker = pygame.time.Clock()

    state        = None
    last_ping    = 0.0
    last_score_flash = 0.0
    flash_msg    = ""

    def apply_prediction(s: dict, move: str):
        """Locally advance our paddle so input feels instant."""
        if s is None:
            return
        idx = player_id
        if move == "UP":
            s["paddles"][idx] -= PADDLE_SPEED
        elif move == "DOWN":
            s["paddles"][idx] += PADDLE_SPEED
        # Clamp
        from common.constants import HEIGHT, PADDLE_HEIGHT
        s["paddles"][idx] = max(0, min(HEIGHT - PADDLE_HEIGHT, s["paddles"][idx]))

    def reconcile(server_state: dict):
        """
        Snap to the server's authoritative state then re-apply any
        inputs the server hasn't acknowledged yet.
        """
        s = dict(server_state)
        s["paddles"] = list(server_state["paddles"])
        for inp in net.pending_inputs:
            apply_prediction(s, inp.get("move", ""))
        return s

    font_wait = pygame.font.Font(None, 36)
    waiting   = True

    while waiting:
        ticker.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.fill((0, 0, 0))
        msg  = "Waiting for game to start…" if not net.started else "Starting!"
        surf = font_wait.render(msg, True, (255, 255, 255))
        screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, HEIGHT // 2))
        pygame.display.flip()

        if net.started:
            waiting = False

        data = net.receive()
        if data and data["type"] == "STATE":
            state = reconcile(data)

    while True:
        ticker.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        now = time.time()
        if now - last_ping > 1.0:
            net.heartbeat()
            last_ping = now

        move = get_input(player_id)
        if move:
            net.send_input(move)
            apply_prediction(state, move)   # immediate local feedback

        data = net.receive()
        if data:
            t = data.get("type")

            if t == "STATE":
                state = reconcile(data)

            elif t == "RESET":
                net.pending_inputs.clear()
                state = data

            elif t == "SCORE":
                sc = data.get("score", [0, 0])
                flash_msg        = f"Score  {sc[0]} – {sc[1]}"
                last_score_flash = time.time()

        if state:
            draw(screen, state, net, player_id)
        else:
            screen.fill((0, 0, 0))

        if time.time() - last_score_flash < 1.5 and flash_msg:
            fnt  = pygame.font.Font(None, 48)
            surf = fnt.render(flash_msg, True, (255, 220, 60))
            screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2,
                               HEIGHT // 2 - 24))

        pygame.display.flip()


if __name__ == "__main__":
    main()