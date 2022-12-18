import pygame
import math


WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 800, 800
FPS = 30
MAPS_DIR = 'maps'
TILE_SIZE = 25
BLACK, WHITE, RED = (0, 0, 0), (255, 255, 255), (255, 0, 0)
GREEN, BLUE, YELLOW = (0, 255, 0), (0, 0, 255), (255, 255, 0)
bullets = []


class Map:
    '''Класс Map создает карту из указанного текстового файла. Карта хранится в переменной self.map в виде матрицы
    Так-же в инициализатор передается список ID тайлов, по которым можно ходить и тайлы-триггеры.'''

    def __init__(self, map_filename, free_tiles, trigger_tiles, spawn_pos):
        self.map = []
        with open(f'{MAPS_DIR}/{map_filename}') as input_map:
            for line in input_map:
                self.map.append(list(map(int, line.split())))
        self.spawn_pos = spawn_pos
        self.height = len(self.map)
        self.width = len(self.map[0])
        self.free_tiles = free_tiles
        self.trigger_tiles = trigger_tiles

    def render(self, screen):  # Отрисовка карты на холсте
        colors = {0: BLACK, 1: GREEN, 2: BLUE, 3: RED, 4: WHITE}
        for y in range(self.height):
            for x in range(self.width):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                screen.fill(colors[self.get_tile_id((x, y))], rect)

    def get_tile_id(self, pos):  # Получает ID тайла по координатам (x, y). Помогает понять его тип
        return self.map[pos[1]][pos[0]]

    def get_tile_coords(self, pos):
        return pos[0] * TILE_SIZE, pos[1] * TILE_SIZE

    def set_spawn_pos(self, pos):
        self.spawn_pos = pos

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
        self.x, self.y = pos[0], pos[1]

    def render(self, screen):  # Отрисовка существа на холсте
        center = self.x * TILE_SIZE + TILE_SIZE // 2, self.y * TILE_SIZE + TILE_SIZE // 2
        pygame.draw.circle(screen, self.color, center, TILE_SIZE // 2)


class Hero(Person):
    '''Класс Игрока, наследуется от Person. Имеет допольнительный атрибут ammo - количество патрон / and smth more...'''
    bullets = []

    def __init__(self, pos, color, ammo):
        super().__init__(pos, color)
        self.pos = pos
        self.color = color
        self.ammo = ammo

    def shoot(self):
        if self.ammo > 0:
            self.ammo -= 1
            pos = self.get_pos()
            bullets.append(Bullet(pos[0] * TILE_SIZE + TILE_SIZE // 2, pos[1] * TILE_SIZE + TILE_SIZE // 2))
        elif self.ammo == 0:
            print('No ammo')  # TODO: Сделать что-то с патронами

    def update_bullets(self, screen):
        for bullet in bullets[:]:
            bullet.update()
            if not screen.get_rect().collidepoint(bullet.pos):
                bullets.remove(bullet)


class Bullet:
    def __init__(self, x, y):
        self.pos = (x, y)
        mx, my = pygame.mouse.get_pos()
        self.dir = (mx - x, my - y)
        length = math.hypot(*self.dir)
        if length == 0.0:
            self.dir = (0, -1)
        else:
            self.dir = (self.dir[0] / length, self.dir[1] / length)
        angle = math.degrees(math.atan2(-self.dir[1], self.dir[0]))

        self.bullet = pygame.Surface((10, 4)).convert_alpha()
        self.bullet.fill(YELLOW)
        self.bullet = pygame.transform.rotate(self.bullet, angle)
        self.speed = 20

    def get_pos(self):
        return self.pos

    def update(self):
        self.pos = (self.pos[0] + self.dir[0] * self.speed,
                    self.pos[1] + self.dir[1] * self.speed)

    def draw(self, surf):
        bullet_rect = self.bullet.get_rect(center=self.pos)
        surf.blit(self.bullet, bullet_rect)

    def get_tile_pos(self, pos):
        bullet_rect = self.bullet.get_rect(center=pos)
        return bullet_rect[0] // TILE_SIZE, bullet_rect[1] // TILE_SIZE


class Game:
    '''Класс Game управляет логикой и ходом игры. При инициализации получает объект карты и объекты существ.'''

    def __init__(self, map, hero):
        self.map = map
        self.hero = hero

    def render(self, screen):  # Синхронизированная отрисовка
        self.map.render(screen)
        self.hero.render(screen)
        self.hero.update_bullets(screen)
        for bullet in bullets:
            if self.check_wall(bullet):
                bullet.draw(screen)
            else:
                bullets.remove(bullet)

    def check_wall(self, bullet):
        if self.map.get_tile_id(bullet.get_tile_pos(bullet.get_pos())) not in self.map.free_tiles:
            return False
        return True

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
        if self.map.get_tile_id(self.hero.get_pos()) in self.map.trigger_tiles:  # Если игрок активировал триггер карты
            triggger_id = self.map.get_tile_id(self.hero.get_pos())
            if triggger_id == 2:  # Смена карты
                self.map.set_spawn_pos((9, 6))
                self.change_map(self.map, 'second_map.txt', [0, 2, 3], [2, 3], self.map.spawn_pos)

    def change_map(self, map_object, map_filename, free_tiles, trigger_tiles, spawn_pos):
        bullets.clear()
        map_object.__init__(map_filename, free_tiles, trigger_tiles, spawn_pos)
        self.hero.set_pos(spawn_pos)


def main():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption('Hot Rooms')

    map = Map('ex_map.txt', [0, 2, 3], [2, 3], (3, 9))
    hero = Hero(map.spawn_pos, WHITE, 10)

    game = Game(map, hero)

    clock = pygame.time.Clock()
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                hero.shoot()
        game.update_hero()
        screen.fill((0, 0, 0))
        game.render(screen)
        pygame.display.flip()
    pygame.quit()


if __name__ == '__main__':
    main()
