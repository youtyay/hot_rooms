import pygame


WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 1920, 1080
FPS = 60
MAPS_DIR = 'maps'
TILE_SIZE = 30
BLACK, WHITE, RED, GREEN, BLUE = (0, 0, 0), (255, 255, 255), (255, 0, 0), (0, 255, 0), (0, 0, 255)


class Map:

    def __init__(self, map_filename, free_tiles, trigger_tiles):
        self.map = []
        with open(f'{MAPS_DIR}/{map_filename}') as input_map:
            for line in input_map:
                self.map.append(list(map(int, line.split())))
        self.height = len(self.map)
        self.width = len(self.map[0])
        self.tile_size = TILE_SIZE
        self.free_tiles = free_tiles
        self.trigger_tiles = trigger_tiles

    def render(self, screen):
        colors = {0: BLACK, 1: GREEN, 2}


def main():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)

    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.fill((0, 0, 0))
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == '__main__':
    main()
