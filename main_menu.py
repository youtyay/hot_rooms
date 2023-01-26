import os

import pygame
import pygame_menu
from pygame_menu import themes
from configparser import ConfigParser


def menu():
    pygame.init()
    surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    config = ConfigParser()
    config.read('config.ini')

    def set_difficulty(value, difficulty):
        config['CONFIG']['difficulty'] = value[0][0]
        print(value[0][0])
        # print(value)
        # print(difficulty)

    def start_the_game():
        for value in mainmenu.get_input_data().values():
            config['CONFIG']['username'] = value
        os.system("start cmd /k python main.py")
        os.system("taskkill /F /IM cmd.exe")
        with open('config.ini', mode='w') as configfile:
            config.write(configfile)
        exit()

    def level_menu():
        mainmenu._open(level)

    mainmenu = pygame_menu.Menu('Welcome', 1536, 864, theme=themes.THEME_DARK)
    mainmenu.add.text_input('Name: ', default=config['CONFIG']['username'])
    mainmenu.add.button('Play', start_the_game)
    mainmenu.add.button('Settings', level_menu)
    mainmenu.add.button('Quit', pygame_menu.events.EXIT)

    level = pygame_menu.Menu('Select a Difficulty', 1536, 864, theme=themes.THEME_DARK)
    level.add.selector('Difficulty :', [('Hard', 1), ('Easy', 2)], onchange=set_difficulty)

    loading = pygame_menu.Menu('Loading the Game...', 1536, 864, theme=themes.THEME_DARK)
    loading.add.progress_bar("Progress", progressbar_id="1", default=0, width=200, )

    arrow = pygame_menu.widgets.LeftArrowSelection(arrow_size=(10, 15))

    update_loading = pygame.USEREVENT + 0

    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == update_loading:
                progress = loading.get_widget("1")
                progress.set_value(progress.get_value() + 1)
                if progress.get_value() == 100:
                    pygame.time.set_timer(update_loading, 0)
            if event.type == pygame.QUIT:
                exit()

        if mainmenu.is_enabled():
            mainmenu.update(events)
            mainmenu.draw(surface)
            if (mainmenu.get_current().get_selected_widget()):
                arrow.draw(surface, mainmenu.get_current().get_selected_widget())

        pygame.display.update()


menu()
