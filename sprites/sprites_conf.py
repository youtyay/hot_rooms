import pygame


def test_tex():
    texture = pygame.image.load("sprites/test_tex.png")
    return texture


def floor_tex():
    texture = pygame.image.load("sprites/floor.png")
    return texture


def walls_tex():
    texture = pygame.image.load("sprites/walls.png")
    return texture


def player1_tex():
    texture = pygame.image.load("sprites/player1.png")
    return texture
