from common.constants import (
    WIDTH, HEIGHT, BALL_SIZE, BALL_SPEED,
    PADDLE_WIDTH, PADDLE_HEIGHT, PADDLE_SPEED,
)

LEFT_PADDLE_X  = 10
RIGHT_PADDLE_X = WIDTH - 20   # = 780


class GameEngine:
    def __init__(self):
        self.score = [0, 0]   # persists across rounds
        self._reset_round()

    def _reset_round(self):
        """Reset ball and paddles only — score is preserved."""
        self.ball_x  = WIDTH  // 2
        self.ball_y  = HEIGHT // 2
        self.ball_dx = BALL_SPEED
        self.ball_dy = BALL_SPEED
        self.paddles = [
            HEIGHT // 2 - PADDLE_HEIGHT // 2,
            HEIGHT // 2 - PADDLE_HEIGHT // 2,
        ]

    def reset(self):
        """Full reset including score (called only at game start)."""
        self.score = [0, 0]
        self._reset_round()

    def update(self) -> str | None:
        """
        Advance physics by one tick.
        Returns "SCORE_LEFT", "SCORE_RIGHT", or None.

        Order of operations:
          1. Move ball.
          2. Bounce off top/bottom walls.
          3. If ball reaches a paddle face, bounce it if the paddle is there;
             otherwise the ball keeps travelling past the paddle.
          4. If the ball reaches the actual screen edge (x<=0 or x+SIZE>=WIDTH),
             award the point — this is the classic Pong scoring rule.
        """
        self.ball_x += self.ball_dx
        self.ball_y += self.ball_dy

        # Top / bottom wall bounce
        if self.ball_y <= 0:
            self.ball_y  = 0
            self.ball_dy = abs(self.ball_dy)

        if self.ball_y + BALL_SIZE >= HEIGHT:
            self.ball_y  = HEIGHT - BALL_SIZE
            self.ball_dy = -abs(self.ball_dy)

        # Left paddle bounce — only while ball is still in the field (x > 0)
        left_face = LEFT_PADDLE_X + PADDLE_WIDTH   # x = 20
        if self.ball_dx < 0 and self.ball_x <= left_face and self.ball_x > 0:
            if self._paddle_hit(0):
                self.ball_x  = left_face            # push clear to avoid retrigger
                self.ball_dx = abs(self.ball_dx)

        # Right paddle bounce — only while ball is still in the field
        right_face = RIGHT_PADDLE_X                 # x = 780
        if (self.ball_dx > 0
                and self.ball_x + BALL_SIZE >= right_face
                and self.ball_x + BALL_SIZE < WIDTH):
            if self._paddle_hit(1):
                self.ball_x  = right_face - BALL_SIZE
                self.ball_dx = -abs(self.ball_dx)

        # Wall scoring — ball reached the screen edge
        if self.ball_x <= 0:
            self.score[1] += 1
            return "SCORE_RIGHT"

        if self.ball_x + BALL_SIZE >= WIDTH:
            self.score[0] += 1
            return "SCORE_LEFT"

        return None

    def move_paddle(self, player: int, direction: str):
        """Move a paddle up or down, clamped to the screen."""
        if direction == "UP":
            self.paddles[player] -= PADDLE_SPEED
        elif direction == "DOWN":
            self.paddles[player] += PADDLE_SPEED

        self.paddles[player] = max(
            0, min(HEIGHT - PADDLE_HEIGHT, self.paddles[player])
        )

    def get_state(self) -> dict:
        return {
            "ball":    {"x": self.ball_x, "y": self.ball_y,
                        "dx": self.ball_dx, "dy": self.ball_dy},
            "paddles": list(self.paddles),
            "score":   list(self.score),
        }

    def reset_state(self) -> dict:
        """Reset ball/paddles for a new round, keep score, return full state."""
        self._reset_round()
        return {"type": "RESET", **self.get_state()}

    def _paddle_hit(self, player: int) -> bool:
        py = self.paddles[player]
        return (self.ball_y + BALL_SIZE >= py and
                self.ball_y <= py + PADDLE_HEIGHT)