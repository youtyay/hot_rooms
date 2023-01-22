import pygame
import math
import pytmx
import configparser
from random import choice

from constants import *


# Вспомогательные переменные для игры
map_number = 1
weapons = []
bullets = []
enemies = []
enemy_hp = ENEMY_HP
enemy_event = False
win = False
lose = False
pistol_image = pygame.image.load('sprites/pistol_clear.png')
shotgun_image = pygame.image.load('sprites/shotgun_clear.png')
one_image = pygame.image.load('sprites/1.png')
two_image = pygame.image.load('sprites/2.png')

# Вспомогательные настройки
hex = False
person_hitbox_view = False
enemy_trigger_size_view = False

# Конфигурация пользователя
config = configparser.ConfigParser()
config.read('config.ini')
username = config['CONFIG']['username']
difficulty = config['CONFIG']['difficulty']
kills = 0


class Map:
    """
    Класс Map создает карту из указанного файла формата *.tmx...

    TODO: Переделать описание класса да и ваще всего кода

    Так-же в инициализатор передается список ID тайлов, по которым можно ходить и тайлы-триггеры.
    """

    def __init__(self, map_filename, free_tiles, trigger_tiles):
        self.map = pytmx.load_pygame(f'{MAPS_DIR}/{map_filename}')
        self.spawn_pos = (0, 0)
        self.height = self.map.height
        self.width = self.map.width
        self.free_tiles = free_tiles
        self.trigger_tiles = trigger_tiles
        self.spawn_enemies()

    def render(self, screen):  # Отрисовка карты на холсте
        for y in range(self.height):
            for x in range(self.width):
                image = self.map.get_tile_image(x, y, 0)
                screen.blit(image, (x * TILE_SIZE, y * TILE_SIZE))
                if hex:  # Белая сетка
                    rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    pygame.draw.rect(screen, WHITE, rect, 1)

    def get_tile_id(self, pos):  # Возвращает ID тайла по координатам (x, y). Помогает понять его тип
        pos_list = list(pos)
        if pos[0] < 0:
            pos_list[0] = 0
        elif pos[0] > 49:
            pos_list[0] = 49
        if pos[1] > 34:
            pos_list[1] = 34
        elif pos[1] < 0:
            pos_list[1] = 0
        return self.map.tiledgidmap[self.map.get_tile_gid(*pos_list, 0)] - 1

    def get_tile_coords(self, pos):  # Возвращает пиксельные координаты тайла
        return pos[0] * TILE_SIZE, pos[1] * TILE_SIZE

    def spawn_enemies(self):          # Спавнит врагов на тайлах спавна мобов. Все объекты создаются в списке enemies,
        for y in range(self.height):  # там они рендерятся и обновляются.
            for x in range(self.width):
                if self.get_tile_id((x, y)) == 16:
                    enemies.append(Enemy((x, y), 'enemy_cultist.png', enemy_hp))
                elif self.get_tile_id((x, y)) == 15:
                    self.spawn_pos = (x, y)

    def is_free(self, pos):  # Проверка на проходимость тайла
        return self.get_tile_id(pos) in self.free_tiles

    def find_path_step(self, start, target):  # Алгоритм поиска кратчайшего пути из тайла start в тайл target.
        INF = 1000                            # Применяется для объектов врага
        x, y = start
        distance = [[INF] * self.width for _ in range(self.height)]
        distance[y][x] = 0
        prev = [[None] * self.width for _ in range(self.height)]
        queue = [(x, y)]
        while queue:
            x, y = queue.pop(0)
            for dx, dy in (0, 1), (1, 0), (-1, 0), (0, -1):
                next_x, next_y = x + dx, y + dy
                if 0 < next_x < self.width and 0 < next_y < self.height and \
                        self.is_free((next_x, next_y)) and distance[next_y][next_x] == INF:
                    distance[next_y][next_x] = distance[y][x] + 1
                    prev[next_y][next_x] = (x, y)
                    queue.append((next_x, next_y))
        x, y = target
        if distance[y][x] == INF or start == target:
            return start
        while prev[y][x] != start:
            x, y = prev[y][x]
        return x, y


class Person:
    """
    Класс Person создаёт сущностей на карте. При инициализации прописывается начальная точка появления
    и текстуру
    """

    def __init__(self, pos, texture, hp):
        super().__init__()
        self.person_texture = pygame.sprite.Sprite()
        self.person_texture.image = pygame.image.load(f'{SPRITES_DIR}/{texture}')
        self.person_texture.rect = self.person_texture.image.get_rect()
        self.x, self.y = pos
        self.pixel_pos = (pos[0] * TILE_SIZE, pos[1] * TILE_SIZE)
        self.hitbox = pygame.Rect(self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self.hp = hp

    def get_pos(self):
        return round(self.pixel_pos[0] / TILE_SIZE), round(self.pixel_pos[1] / TILE_SIZE)

    def set_pos(self, pos):
        self.x, self.y = pos[0], pos[1]
        self.set_pixel_pos((self.x * TILE_SIZE, self.y * TILE_SIZE))
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
            pygame.draw.rect(screen, GREEN, self.hitbox, 1)


class Enemy(Person):  # TODO: пофиксить стак врагов в одном тайле

    def __init__(self, pos, texture, hp):
        super().__init__(pos, texture, hp)
        self.pos = pos
        self.triggering = False
        self.trigger_rect = self.get_rect()
        self.trigger_rect.height = self.trigger_rect.width = ENEMY_TRIGGER_SIZE * TILE_SIZE
        self.trigger_rect.center = (self.pixel_pos[0] + TILE_SIZE // 2, self.pixel_pos[1] + TILE_SIZE // 2)

    def render(self, screen):
        super(Enemy, self).render(screen)
        if difficulty == 'Easy':
            rect = pygame.Rect(self.pixel_pos[0], self.pixel_pos[1] - 6, self.hp, 5)
            pygame.draw.rect(screen, RED, pygame.Rect(self.pixel_pos[0], self.pixel_pos[1] - 6, ENEMY_HP, 5))
            pygame.draw.rect(screen, GREEN, rect)
        elif difficulty == 'Hard':
            rect = pygame.Rect(self.pixel_pos[0], self.pixel_pos[1] - 6, self.hp // 2, 5)
            pygame.draw.rect(screen, RED, pygame.Rect(self.pixel_pos[0], self.pixel_pos[1] - 6, ENEMY_HP, 5))
            pygame.draw.rect(screen, GREEN, rect)
        if enemy_trigger_size_view:
            pygame.draw.rect(screen, RED, self.trigger_rect, 1)

    def trigger_hero(self):
        self.trigger_rect.center = (self.pixel_pos[0] + TILE_SIZE // 2, self.pixel_pos[1] + TILE_SIZE // 2)


class Hero(Person):  # TODO: создать разнообразные пушки для игрока :)
    """
    Класс Игрока, наследуется от Person. Имеет допольнительный атрибут ammo - количество патрон / and smth more...
    """

    def __init__(self, pos, texture, hp, ammo):
        super().__init__(pos, texture, hp)
        self.person_texture.image = pygame.image.load(f'{SPRITES_DIR}/{texture}').convert_alpha()
        self.pos = pos
        self.ammo = ammo
        self.weapon = None
        self.aiming = False
        self.alive = True
        self.image = self.person_texture.image

    def render(self, screen):
        screen.blit(self.image, self.pixel_pos)
        font = pygame.font.Font(None, 13)
        text = font.render(username, True, WHITE)
        screen.blit(text, (self.pixel_pos[0], self.pixel_pos[1] - 8))
        if person_hitbox_view:
            pygame.draw.rect(screen, GREEN, self.hitbox, 1)
        if self.aiming:
            pygame.draw.line(screen, GREEN, self.get_rect().center, pygame.mouse.get_pos(), 1)

    def rotate(self):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        rel_x, rel_y = mouse_x - self.pixel_pos[0], mouse_y - self.pixel_pos[1]
        angle = math.degrees(math.atan2(-rel_x, -rel_y))
        self.image = pygame.transform.rotate(self.person_texture.image, int(angle))
        self.person_texture.rect = self.image.get_rect(center=self.pixel_pos)

    def shoot(self):
        pos = self.get_pixel_pos()
        if self.ammo > 0:
            if self.weapon == 'pistol':
                bullets.append(Bullet(pos[0] + TILE_SIZE // 2, pos[1] + TILE_SIZE // 2))
                self.ammo -= 1
            elif self.weapon == 'shotgun':
                bullets.append(Bullet(pos[0] + TILE_SIZE // 2, pos[1] + TILE_SIZE // 2, deviation=50))
                bullets.append(Bullet(pos[0] + TILE_SIZE // 2, pos[1] + TILE_SIZE // 2))
                bullets.append(Bullet(pos[0] + TILE_SIZE // 2, pos[1] + TILE_SIZE // 2, deviation=-50))
                self.ammo -= 3
            print('Ammo:', self.ammo)
        else:
            print('No ammo')  # TODO: Сделать что-то с патронами

    def aim(self):
        self.aiming = not self.aiming

    def update_bullets(self, screen):
        for bullet in bullets[:]:
            bullet.update()
            if not screen.get_rect().collidepoint(bullet.pos):
                bullets.remove(bullet)


class Bullet:
    """
    TODO: Сделать описание класса пули
    """
    def __init__(self, x, y, deviation=None):
        self.pos = (x, y)
        self.deviation = deviation
        mx, my = pygame.mouse.get_pos()
        if self.deviation:
            if mx > x and my > y or mx < x and my < y:
                self.dir = (mx - x - self.deviation, my - y + self.deviation)
            else:
                self.dir = (mx - x + self.deviation, my - y + self.deviation)
        else:
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
        self.speed = BULLET_SPEED
        self.rect = self.bullet.get_rect()

    def get_pos(self):
        return self.pos

    def get_rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.bullet.get_width(), self.bullet.get_height())

    def update(self):
        self.pos = (self.pos[0] + self.dir[0] * self.speed,
                    self.pos[1] + self.dir[1] * self.speed)

    def draw(self, screen):
        bullet_rect = self.bullet.get_rect(center=self.pos)
        screen.blit(self.bullet, bullet_rect)

    def get_tile_pos(self, pos):
        bullet_rect = self.bullet.get_rect(center=pos)
        return bullet_rect[0] // TILE_SIZE, bullet_rect[1] // TILE_SIZE


class Game:
    """
    Класс Game управляет логикой и ходом игры. При инициализации получает объект карты и объекты существ.
    """

    def __init__(self, map, hero):
        self.map = map
        self.hero = hero

    def render(self, screen):  # Синхронизированная отрисовка
        global enemy_event, kills, lose
        self.map.render(screen)
        self.hero.render(screen)
        hero_rect = self.hero.get_rect()
        for enemy in enemies:
            if hero_rect.colliderect(enemy.trigger_rect):
                enemy.triggering = True
            else:
                enemy.triggering = False
            if enemy.get_rect().colliderect(hero_rect):
                self.hero.alive = False
                lose = True
            if self.check_enemy_for_bullet(enemy):
                if enemy.triggering and enemy_event:
                    self.move_enemy(enemy)
                    enemy.trigger_hero()
                enemy.render(screen)
            else:
                if self.hero.weapon == 'pistol':
                    enemy.hp -= PISTOL_DAMAGE
                elif self.hero.weapon == 'shotgun':
                    enemy.hp -= SHOTGUN_DAMAGE
                print(f'{enemy} wounded   HP:{enemy.hp}')
                if enemy.hp <= 0:
                    kills += 1
                    enemies.remove(enemy)
                    print(f'{enemy} killed')
        enemy_event = False
        self.hero.update_bullets(screen)
        font = pygame.font.Font(None, 20)
        hero_ammo = font.render(f'Ammo: {self.hero.ammo}', True, (100, 255, 100))
        hero_kills = font.render(f'Kills: {kills}', True, (100, 255, 100))
        if weapons:
            if len(weapons) >= 1 and 'pistol' in weapons:
                screen.blit(one_image, (1290, 500))
                screen.blit(pistol_image, (1330, 500))
            if len(weapons) >= 2 and 'shotgun' in weapons:
                screen.blit(two_image, (1290, 600))
                screen.blit(shotgun_image, (1330, 600))
        screen.blit(hero_ammo, (1330, 200))
        screen.blit(hero_kills, (1330, 300))
        for bullet in bullets:
            if self.check_wall_for_bullet(bullet):
                bullet.draw(screen)
            else:
                bullets.remove(bullet)

    def check_enemy_for_bullet(self, enemy):
        for bullet in bullets:
            if bullet.get_rect().colliderect(enemy.get_rect()):
                bullets.remove(bullet)
                return False
        return True

    def check_wall_for_bullet(self, bullet):  # Проверка на стену для пули
        if self.map.get_tile_id(bullet.get_tile_pos(bullet.get_pos())) not in self.map.free_tiles:
            return False
        return True

    def check_wall_for_player(self, next_pixel_x, next_pixel_y):  # Проверка на стену для игрока
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

    def update_hero(self):  # Обработка Игрока
        global map_number, win

        self.hero.rotate()

        next_pixel_x, next_pixel_y = self.hero.get_pixel_pos()
        key = pygame.key.get_pressed()

        if key[pygame.K_1]:
            if len(weapons) >= 1:
                self.hero.weapon = weapons[0]
        if key[pygame.K_2]:
            if len(weapons) >= 2:
                self.hero.weapon = weapons[1]

        if key[pygame.K_a] or key[pygame.K_LEFT]:
            next_pixel_x -= MOVE_SPEED
        if key[pygame.K_d] or key[pygame.K_RIGHT]:
            next_pixel_x += MOVE_SPEED
        if key[pygame.K_w] or key[pygame.K_UP]:
            next_pixel_y -= MOVE_SPEED
        if key[pygame.K_s] or key[pygame.K_DOWN]:
            next_pixel_y += MOVE_SPEED

        self.hero.set_pixel_pos(self.check_wall_for_player(next_pixel_x, next_pixel_y))

        if self.map.get_tile_id(self.hero.get_pos()) in self.map.trigger_tiles:  # Если игрок активировал триггер карты
            triggger_id = self.map.get_tile_id(self.hero.get_pos())
            if triggger_id == 8:  # Смена карты
                map_number += 1
                self.change_map(self.map, f'map{map_number}.tmx', [0, 8, 16, 13, 7, 15, 23], [7, 8, 13, 23])
            if triggger_id == 13:
                win = True
            if triggger_id == 7:
                if 'pistol' not in weapons:
                    weapons.append('pistol')
            if triggger_id == 23:
                if 'shotgun' not in weapons:
                    weapons.append('shotgun')

    def move_enemy(self, enemy):  # TODO: Пофиксить кривое перермещение врагов по тайлам (сделать плавное пиксельное)
        enemy_pos = enemy.get_pos()
        enemy_pixel_pos = list(enemy.get_pixel_pos())
        next_pos = self.map.find_path_step(enemy_pos, self.hero.get_pos())
        direction = 'stay'
        if next_pos[0] > enemy_pos[0]:
            direction = 'right'
        elif next_pos[0] < enemy_pos[0]:
            direction = 'left'
        elif next_pos[1] > enemy_pos[1]:
            direction = 'down'
        elif next_pos[1] < enemy_pos[1]:
            direction = 'up'
        dt = 5
        for i in range(5):
            if direction == 'right':
                enemy_pixel_pos[0] += dt
            elif direction == 'left':
                enemy_pixel_pos[0] -= dt
            elif direction == 'down':
                enemy_pixel_pos[1] += dt
            elif direction == 'up':
                enemy_pixel_pos[1] -= dt
            enemy.set_pixel_pos(enemy_pixel_pos)

    def change_map(self, map_object, map_filename, free_tiles, trigger_tiles):
        bullets.clear()
        enemies.clear()
        print(f'map{map_number - 1} changed to map{map_number}')
        map_object.__init__(map_filename, free_tiles, trigger_tiles)
        self.hero.set_pos(map_object.spawn_pos)


def main():
    global enemy_event, enemy_hp

    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.init()
    clock = pygame.time.Clock()
    pygame.time.set_timer(ENEMY_EVENT_TYPE, ENEMY_DELAY)
    pygame.display.set_caption('Hot Rooms')
    screen = pygame.display.set_mode(WINDOW_SIZE, pygame.FULLSCREEN)

    if difficulty == 'Hard':
        enemy_hp *= 2

    font = pygame.font.Font(None, 200)

    map = Map(f'map{map_number}.tmx', [0, 8, 16, 13, 7, 15, 23], [7, 8, 13, 23])
    hero = Hero(map.spawn_pos, 'hero.png', PLAYER_HP, 1000)

    game = Game(map, hero)

    track = choice(PLAYLIST)
    pygame.mixer.music.load(track)
    print(f'Now playing: {track}')
    PLAYLIST.remove(track)
    track = choice(PLAYLIST)
    pygame.mixer.music.queue(track)
    PLAYLIST.remove(track)
    pygame.mixer.music.set_endevent(pygame.USEREVENT)
    pygame.mixer.music.play()

    running = True
    count = 0
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if weapons:
                        hero.shoot()
                if event.button == 3:
                    hero.aim()
            if event.type == pygame.KEYDOWN:
                if pygame.key.get_pressed()[pygame.K_ESCAPE]:
                    exit('Game closed')
            if event.type == ENEMY_EVENT_TYPE:
                enemy_event = True
            if event.type == pygame.USEREVENT:
                print(f'Now playing: {track}')
                if len(PLAYLIST) > 0:
                    track = choice(PLAYLIST)
                    pygame.mixer.music.queue(track)
                    PLAYLIST.remove(track)
        screen.fill((0, 0, 0))
        if win:
            text = font.render("Victory!", True, GREEN)
            text_x = WINDOW_WIDTH // 2.5 - text.get_width() // 2
            text_y = WINDOW_HEIGHT // 2.5 - text.get_height() // 2
            screen.blit(text, (text_x, text_y))
        elif lose:
            text = font.render("Defeat", True, RED)
            text_x = WINDOW_WIDTH // 2.5 - text.get_width() // 2
            text_y = WINDOW_HEIGHT // 2.5 - text.get_height() // 2
            screen.blit(text, (text_x, text_y))
        else:
            game.update_hero()
            game.render(screen)
        pygame.display.flip()
        count += 1
        if count % FPS == 0:
            if count // FPS % 60 < 10:
                time = f'{count // FPS // 60}:0{count // FPS % 60}'
            else:
                time = f'{count // FPS // 60}:{count // FPS % 60}'
            print('FPS:', int(clock.get_fps()), '   time:', time)


if __name__ == '__main__':
    main()
    pygame.quit()
