import pygame
from common.constants import WIDTH, HEIGHT, PADDLE_WIDTH, PADDLE_HEIGHT, BALL_SIZE

WHITE  = (255, 255, 255)
GRAY   = (160, 160, 160)
YELLOW = (255, 220, 60)
BLACK  = (0,   0,   0)


def draw(screen: pygame.Surface, state: dict, net, player_id: int):
    screen.fill(BLACK)

    for y in range(0, HEIGHT, 20):
        pygame.draw.rect(screen, GRAY, (WIDTH // 2 - 1, y, 2, 10))

    paddles = state["paddles"]
    ball    = state["ball"]
    score   = state["score"]

    pygame.draw.rect(screen, WHITE, (10, paddles[0], PADDLE_WIDTH, PADDLE_HEIGHT))

    pygame.draw.rect(screen, WHITE, (WIDTH - 20, paddles[1], PADDLE_WIDTH, PADDLE_HEIGHT))

    pygame.draw.rect(screen, WHITE, (ball["x"], ball["y"], BALL_SIZE, BALL_SIZE))

    font_big = pygame.font.Font(None, 72)
    left_s   = font_big.render(str(score[0]), True, WHITE)
    right_s  = font_big.render(str(score[1]), True, WHITE)
    screen.blit(left_s,  (WIDTH // 4 - left_s.get_width()  // 2, 20))
    screen.blit(right_s, (3 * WIDTH // 4 - right_s.get_width() // 2, 20))

    font_sm = pygame.font.Font(None, 22)
    hud = [
        f"Player {player_id + 1}",
        f"Latency : {net.latency:5.1f} ms",
        f"Jitter  : {net.jitter:5.1f} ms",
    ]
    for i, line in enumerate(hud):
        color  = YELLOW if i == 0 else GRAY
        surf   = font_sm.render(line, True, color)
        screen.blit(surf, (10, HEIGHT - 20 - (len(hud) - i) * 22))