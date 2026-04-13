import pygame


def get_input(player_id: int) -> str | None:
    """
    Return "UP", "DOWN", or None.
    Player 0 → W / S keys.   Player 1 → Arrow Up / Down.
    Keyboard repeat is intentionally not filtered so held keys stream moves.
    """
    keys = pygame.key.get_pressed()

    if player_id == 0:
        if keys[pygame.K_w]:
            return "UP"
        if keys[pygame.K_s]:
            return "DOWN"
    else:
        if keys[pygame.K_UP]:
            return "UP"
        if keys[pygame.K_DOWN]:
            return "DOWN"

    return None
