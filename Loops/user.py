from Utils.utils import draw_user_list, draw_text, get_press_button, get_user_input, get_text_input, wipe_pygame_screen, \
    update_pygame_screen, get_pygame_screen_size
import pygame
from Database.db import show_current_users, get_user_info, check_if_name_in_db, add_user_to_db
import time
from main import fuel_capacity

# User info
user_name = ""
user_id = ""
logged_in = ""
location = ""
co2_consumed = ""
co2_budget = ""

def user_menu(screen, font):
    data_list = show_current_users()
    input_text = ""
    key_list = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]
    active = True

    while active:
        wipe_pygame_screen(screen)
        screen_width, screen_height = get_pygame_screen_size(screen)
        menu = ["1 - Tee uusi pelaaja", "2 - Valitse pelaaja",
                "3 - Aloita peli", "4 - Käyttäjälista"]
        y_start = 100
        y_offset = 50
        max_width = max(font.size(item)[0] for item in menu)

        for i, item in enumerate(menu):
            text_surface = font.render(item, True, (255, 255, 255))
            text_x = (screen_width - max_width) // 2
            text_y = y_start + i * y_offset
            screen.blit(text_surface, (text_x, text_y))

        #draw_text(screen, "1 - Tee uusi pelaaja", 80, 30, font)
        #draw_text(screen, "2 - Valitse pelaaja", 80, 60, font)
        #draw_text(screen, "3 - Aloita peli", 80, 90, font)
        #draw_text(screen, "4 - Käyttäjälista", 80, 120, font)
        #draw_text(screen, input_text, 80, 120, font)
        update_pygame_screen()

        char = get_press_button(key_list)
        if char == pygame.K_1:
            add_user(screen, font)
        elif char == pygame.K_2:
            select_user(screen, font)
        elif char == pygame.K_3:
            active = False
        elif char == pygame.K_4:
            print("4 painettu")
            draw_user_list(screen, font, data_list)

    return input_text.strip()

# Käyttäjän valinta
def select_user(screen, font):
    input_text = ""
    active = True

    while active:
        wipe_pygame_screen(screen)
        draw_text(screen, "Nimi: ", 80, 30, font)
        draw_text(screen, input_text, 80, 60, font)
        update_pygame_screen()

        input_text, active = get_user_input(input_text, active, False)

    result = get_user_info(input_text)
    if result:
        user_id = result[0]
        user_name = result[1]
        wipe_pygame_screen(screen)
        draw_text(screen, f"Käyttäjä {user_name} kirjautunut sisään", 80, 30, font)
        update_pygame_screen()
        time.sleep(2)


def add_user(screen, font):
    user_name = get_text_input(screen, font, "Nimi: ", False)
    result = check_if_name_in_db(user_name)
    wipe_pygame_screen(screen)
    if not result:
        add_user_to_db(user_name, fuel_capacity)
        draw_text(screen, f"Käyttäjä {user_name} lisätty tietokantaan", 80, 30, font)
    else:
        draw_text(screen, f"Käyttäjä {user_name} löytyy jo tietokannasta", 80, 30, font)
    update_pygame_screen()
    time.sleep(2)