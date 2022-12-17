import pygame


WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 800, 800
FPS = 30
MAPS_DIR = 'maps'
TILE_SIZE = 25
BLACK, WHITE, RED, GREEN, BLUE = (0, 0, 0), (255, 255, 255), (255, 0, 0), (0, 255, 0), (0, 0, 255)


class Map:
    '''Класс Map создает карту из указанного текстового файла. Карта хранится в переменной self.map в виде матрицы
    Так-же в инициализатор передается список ID тайлов, по которым можно ходить и тайл-триггер.'''

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

    def render(self, screen):  # Отрисовка карты на холсте
        colors = {0: BLACK, 1: GREEN, 2: BLUE, 3: RED, 4: WHITE}
        for y in range(self.height):
            for x in range(self.width):
                rect = pygame.Rect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
                screen.fill(colors[self.get_tile_id((x, y))], rect)

    def get_tile_id(self, pos):  # Получает ID тайла по координатам (x, y). Помогает понять его тип
        return self.map[pos[1]][int(pos[0])]

    def is_free(self, pos):  # Проверка на проходимость тайла
        return self.get_tile_id(pos) in self.free_tiles


class Person:
    '''Класс Person создаёт сущностей на карте. При инициализации прописывается начальная точка появления
    и цвет (позже заменить на текстуру)'''

    def __init__(self, pos, color):
        self.x, self.y = pos
        self.color = color

    def get_pos(self):
        return self.x, self.y

    def set_pos(self, pos):
        self.x, self.y = int(pos[0]), int(pos[1])

    def render(self, screen):  # Отрисовка существа на холсте
        center = self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2
        pygame.draw.circle(screen, self.color, center, TILE_SIZE // 2)


class Game:
    '''Класс Game управляет логикой и ходом игры. При инициализации получает объект карты и объекты существ.'''

    def __init__(self, map, hero):
        self.map = map
        self.hero = hero

    def render(self, screen):  # Синхронизированная отрисовка
        self.map.render(screen)
        self.hero.render(screen)

    def update_hero(self):  # Передвижение Игрока
        next_x, next_y = self.hero.get_pos()
        if pygame.key.get_pressed()[pygame.K_a] or pygame.key.get_pressed()[pygame.K_LEFT]:
            next_x -= 1
        if pygame.key.get_pressed()[pygame.K_d] or pygame.key.get_pressed()[pygame.K_RIGHT]:
            next_x += 1
        if pygame.key.get_pressed()[pygame.K_w] or pygame.key.get_pressed()[pygame.K_UP]:
            next_y -= 1
        if pygame.key.get_pressed()[pygame.K_s] or pygame.key.get_pressed()[pygame.K_DOWN]:
            next_y += 1
        if self.map.is_free((next_x, next_y)):  # Проверка на стену
            self.hero.set_pos((next_x, next_y))


def main():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption('Hot Rooms')

    map = Map('ex_map.txt', [0, 2], 2)
    hero = Person((3, 9), WHITE)

    game = Game(map, hero)

    clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        game.update_hero()
        screen.fill((0, 0, 0))
        game.render(screen)
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == '__main__':
    main()
