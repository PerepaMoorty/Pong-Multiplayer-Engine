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

        if self.ball_y <= 0 or self.ball_y >= HEIGHT:
            self.ball_dy *= -1

        if self.ball_x <= 20:
            if abs(self.ball_y - self.paddles[0]) < PADDLE_HEIGHT // 2:
                self.ball_dx *= -1
            else:
                self.score[1] += 1
                return "RESET"

        if self.ball_x >= WIDTH - 20:
            if abs(self.ball_y - self.paddles[1]) < PADDLE_HEIGHT // 2:
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

    def get_state(self):
        return {
            "ball": {"x": self.ball_x, "y": self.ball_y},
            "paddles": self.paddles,
            "score": self.score
        }
    
    def reset_state(self):
        self.reset()
        return {
            "type": "RESET",
            **self.get_state()
        }