import pygame

def get_input():
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        return "UP"
    if keys[pygame.K_DOWN]:
        return "DOWN"
    return None