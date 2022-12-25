import pygame
import math
import pytmx


WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 800, 800
FPS = 30
MAPS_DIR = 'maps'
SPRITES_DIR = 'sprites'
TILE_SIZE = 25
bullets = []
MOVE_SPEED = 5

BLACK, WHITE, RED = (0, 0, 0), (255, 255, 255), (255, 0, 0)
GREEN, BLUE, YELLOW = (0, 255, 0), (0, 0, 255), (255, 255, 0)
colors = {0: BLACK, 1: GREEN, 2: BLUE, 3: RED, 4: WHITE}

map_textures = {0: 'floor.png', 1: 'walls.png',  2: 'floor.png', 3: 'floor.png', 4: 'floor.png'}
textured = False
hex = False
person_hitbox_view = False

all_sprites_group = pygame.sprite.Group()
map_sprites_group = pygame.sprite.Group()
persons_sprites_group = pygame.sprite.Group()


class Map(pygame.sprite.Group):
    '''Класс Map создает карту из указанного текстового файла. Карта хранится в переменной self.map в виде матрицы
    Так-же в инициализатор передается список ID тайлов, по которым можно ходить и тайлы-триггеры.'''

    def __init__(self, map_filename, free_tiles, trigger_tiles, spawn_pos, group):
        super().__init__(group)
        self.map = pytmx.load_pygame(f'{MAPS_DIR}/{map_filename}')
        self.spawn_pos = spawn_pos
        self.height = self.map.height
        self.width = self.map.width
        self.free_tiles = free_tiles
        self.trigger_tiles = trigger_tiles

    def render(self, screen):  # Отрисовка карты на холсте
        for y in range(self.height):
            for x in range(self.width):
                image = self.map.get_tile_image(x, y, 0)
                screen.blit(image, (x * TILE_SIZE, y * TILE_SIZE))
                # rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                # if textured:
                #     texture = pygame.sprite.Sprite()
                #     texture.image = pygame.image.load(f'{SPRITES_DIR}/{map_textures[self.get_tile_id((x, y))]}')
                #     screen.blit(texture.image, rect)
                #     all_sprites_group.add(texture)
                #     self.map_mask = pygame.mask.from_surface(texture.image)
                # else:
                #     screen.fill(colors[self.get_tile_id((x, y))], rect)
                if hex:  # Белая сетка
                    rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    pygame.draw.rect(screen, WHITE, rect, 1)

    def get_tile_id(self, pos):  # Возвращает ID тайла по координатам (x, y). Помогает понять его тип
        return self.map.tiledgidmap[self.map.get_tile_gid(*pos, 0)] - 1

    def get_tile_coords(self, pos):  # Возвращает пиксельные координаты тайла
        return pos[0] * TILE_SIZE, pos[1] * TILE_SIZE

    def set_spawn_pos(self, pos):
        self.spawn_pos = pos

    def is_free(self, pos):  # Проверка на проходимость тайла
        return self.get_tile_id(pos) in self.free_tiles


class Person(pygame.sprite.Sprite):
    '''Класс Person создаёт сущностей на карте. При инициализации прописывается начальная точка появления
    и цвет (позже заменить на текстуру)'''

    def __init__(self, pos, color, texture, group):
        super().__init__(group)
        self.person_texture = pygame.sprite.Sprite()
        self.person_texture.image = pygame.image.load(f'{SPRITES_DIR}/{texture}')
        self.person_texture.rect = self.person_texture.image.get_rect()
        all_sprites_group.add(self.person_texture)
        self.x, self.y = pos
        self.pixel_pos = (pos[0] * TILE_SIZE, pos[1] * TILE_SIZE)
        self.color = color
        self.hitbox = pygame.Rect(self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

    def get_pos(self):
        return round(self.pixel_pos[0] / TILE_SIZE), round(self.pixel_pos[1] / TILE_SIZE)

    def set_pos(self, pos):
        self.x, self.y = pos[0], pos[1]
        self.hitbox = pygame.Rect(*self.pixel_pos, TILE_SIZE, TILE_SIZE)

    def set_pixel_pos(self, pixel_pos):
        self.pixel_pos = pixel_pos
        self.hitbox = pygame.Rect(*self.pixel_pos, TILE_SIZE, TILE_SIZE)

    def get_pixel_pos(self):
        return self.pixel_pos

    def get_rect(self):
        return pygame.Rect(*self.pixel_pos, TILE_SIZE, TILE_SIZE)

    def render(self, screen):  # Отрисовка существа на холсте
        screen.blit(self.person_texture.image, self.pixel_pos)
        if person_hitbox_view:  # Hitbox существа
            pygame.draw.rect(screen, RED, self.hitbox, 1)


class Hero(Person):
    '''Класс Игрока, наследуется от Person. Имеет допольнительный атрибут ammo - количество патрон / and smth more...'''
    bullets = []

    def __init__(self, pos, color, texture, group, ammo):
        super().__init__(pos, color, texture, group)
        self.player1_texture = pygame.sprite.Sprite()
        self.player1_texture.image = pygame.image.load(f'{SPRITES_DIR}/{texture}')
        self.player1_texture.rect = self.player1_texture.image.get_rect()
        all_sprites_group.add(self.player1_texture)
        self.pos = pos
        self.color = color
        self.ammo = ammo

    def shoot(self):
        if self.ammo > 0:
            self.ammo -= 1
            pos = self.get_pixel_pos()
            bullets.append(Bullet(pos[0] + TILE_SIZE // 2, pos[1] + TILE_SIZE // 2))
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


class Game:  # TODO: Сделать Game главной группой спрайтов и переработать render()
    '''Класс Game управляет логикой и ходом игры. При инициализации получает объект карты и объекты существ.'''

    def __init__(self, map, hero):
        self.map = map
        self.hero = hero

    def render(self, screen):  # Синхронизированная отрисовка
        self.map.render(screen)
        self.hero.render(screen)
        self.hero.update_bullets(screen)
        for bullet in bullets:
            if self.check_wall_for_bullet(bullet):
                bullet.draw(screen)
            else:
                bullets.remove(bullet)

    def check_wall_for_bullet(self, bullet):
        if self.map.get_tile_id(bullet.get_tile_pos(bullet.get_pos())) not in self.map.free_tiles:
            return False
        return True

    def check_wall_for_player(self, next_pixel_x, next_pixel_y):
        tile = (round(next_pixel_x / TILE_SIZE), round(next_pixel_y / TILE_SIZE))
        player_hitbox_rect = self.hero.get_rect()
        for y in range(tile[1] - 1, tile[1] + 2):
            for x in range(tile[0] - 1, tile[0] + 2):
                if self.map.get_tile_id((x, y)) not in self.map.free_tiles:
                    wall_tile = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if wall_tile.colliderect(player_hitbox_rect):
                        if wall_tile.collidepoint(player_hitbox_rect.midleft):
                            next_pixel_x += MOVE_SPEED
                        if wall_tile.collidepoint(player_hitbox_rect.midright):
                            next_pixel_x -= MOVE_SPEED
                        if wall_tile.collidepoint(player_hitbox_rect.midtop):
                            next_pixel_y += MOVE_SPEED
                        if wall_tile.collidepoint(player_hitbox_rect.midbottom):
                            next_pixel_y -= MOVE_SPEED
        return next_pixel_x, next_pixel_y

    def update_hero(self):  # Передвижение Игрока
        next_pixel_x, next_pixel_y = self.hero.get_pixel_pos()
        if pygame.key.get_pressed()[pygame.K_a] or pygame.key.get_pressed()[pygame.K_LEFT]:
            next_pixel_x -= MOVE_SPEED
        if pygame.key.get_pressed()[pygame.K_d] or pygame.key.get_pressed()[pygame.K_RIGHT]:
            next_pixel_x += MOVE_SPEED
        if pygame.key.get_pressed()[pygame.K_w] or pygame.key.get_pressed()[pygame.K_UP]:
            next_pixel_y -= MOVE_SPEED
        if pygame.key.get_pressed()[pygame.K_s] or pygame.key.get_pressed()[pygame.K_DOWN]:
            next_pixel_y += MOVE_SPEED
        self.hero.set_pixel_pos(self.check_wall_for_player(next_pixel_x, next_pixel_y))
        if self.map.get_tile_id(self.hero.get_pos()) in self.map.trigger_tiles:  # Если игрок активировал триггер карты
            triggger_id = self.map.get_tile_id(self.hero.get_pos())
            if triggger_id == 2:  # Смена карты
                self.map.set_spawn_pos((9, 6))
                self.change_map(self.map, 'second_map.txt', [0, 2, 3], [2, 3], self.map.spawn_pos, all_sprites_group)

    def change_map(self, map_object, map_filename, free_tiles, trigger_tiles, spawn_pos, group):
        bullets.clear()
        map_object.__init__(map_filename, free_tiles, trigger_tiles, spawn_pos, group)
        self.hero.set_pos(spawn_pos)


def main():
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode(WINDOW_SIZE)

    map = Map('map1.tmx', [0, 2, 3], [2], (1, 1), all_sprites_group)
    hero = Hero(map.spawn_pos, WHITE, 'player1.png', all_sprites_group, 1000)

    game = Game(map, hero)

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
        pygame.display.set_caption('Hot Rooms ' + str(int(clock.get_fps())) + ' FPS')
    pygame.quit()


if __name__ == '__main__':
    main()
