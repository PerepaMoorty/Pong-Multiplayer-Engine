from common.constants import *

class GameEngine:
    def __init__(self):
        self.reset()

    def reset(self):
        self.ball_x = WIDTH // 2
        self.ball_y = HEIGHT // 2
        self.ball_dx = BALL_SPEED
        self.ball_dy = BALL_SPEED

        self.paddles = [HEIGHT // 2, HEIGHT // 2]
        self.score = [0, 0]

    def update(self):
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy

        # top/bottom walls
        if self.ball_y <= 0:
            self.ball_y = 0
            self.ball_dy *= -1

        if self.ball_y + BALL_SIZE >= HEIGHT:
            self.ball_y = HEIGHT - BALL_SIZE
            self.ball_dy *= -1

        # left paddle
        if self.ball_x <= 20:
            paddle_y = self.paddles[0]

            if (self.ball_y + BALL_SIZE >= paddle_y and
                self.ball_y <= paddle_y + PADDLE_HEIGHT):
                self.ball_x = 20
                self.ball_dx *= -1
            else:
                self.score[1] += 1
                return "RESET"

        # right paddle
        if self.ball_x + BALL_SIZE >= WIDTH - 20:
            paddle_y = self.paddles[1]

            if (self.ball_y + BALL_SIZE >= paddle_y and
                self.ball_y <= paddle_y + PADDLE_HEIGHT):
                self.ball_x = WIDTH - 20 - BALL_SIZE
                self.ball_dx *= -1
            else:
                self.score[0] += 1
                return "RESET"

        return None

    def move_paddle(self, player, direction):
        if direction == "UP":
            self.paddles[player] -= PADDLE_SPEED
        elif direction == "DOWN":
            self.paddles[player] += PADDLE_SPEED

        self.paddles[player] = max(
            0, min(HEIGHT - PADDLE_HEIGHT, self.paddles[player])
        )

    def get_state(self):
        return {
            "ball": {
                "x": self.ball_x,
                "y": self.ball_y,
                "dx": self.ball_dx,
                "dy": self.ball_dy
            },
            "paddles": self.paddles,
            "score": self.score
        }

    def reset_state(self):
        self.reset()
        return {
            "type": "RESET",
            **self.get_state()
        }