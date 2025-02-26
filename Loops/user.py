from Utils.utils import draw_user_list, draw_text, press_button_list, get_user_input, get_text_input, wipe_pygame_screen, \
    update_pygame_screen, get_pygame_screen_size, press_button
import pygame
from Database.db import show_current_users, get_user_info, check_if_name_in_db, add_user_to_db, check_if_logged_in
import time

# User info
user_name = ""
user_id = ""
logged_in = ""
location = ""
co2_consumed = ""
co2_budget = ""

def user_menu(screen, font):
    global user_id, user_name

    key_list = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]
    active = True

    while active:
        wipe_pygame_screen(screen)
        screen_width, screen_height = get_pygame_screen_size(screen)
        data_list = show_current_users()
        logged_in_user_text(screen, font)

        menu = ["1 - Tee uusi pelaaja", "2 - Valitse pelaaja",
                "3 - Aloita peli", "4 - Käyttäjälista" , "5 - Lopeta"]
        y_start = 100
        y_offset = 50
        max_width = max(font.size(item)[0] for item in menu)
        for i, item in enumerate(menu):
            text_surface = font.render(item, True, (255, 255, 255))
            text_x = (screen_width - max_width) // 2
            text_y = y_start + i * y_offset
            screen.blit(text_surface, (text_x, text_y))

        update_pygame_screen()

        char = press_button_list(key_list)
        if char == pygame.K_1:
            add_new_user(screen, font)
        elif char == pygame.K_2:
            select_user(screen, font)
        elif char == pygame.K_3:
            active = False
        elif char == pygame.K_4:
            print("4 painettu")
            draw_user_list(screen, font, data_list)
        elif char == pygame.K_5:
            pygame.quit()

# Käyttäjän valinta
def select_user(screen, font):
    global user_id, user_name
    input_text = ""
    active = True

    while active:
        wipe_pygame_screen(screen)
        draw_text(screen, "ESC", 5, 5, font)
        draw_text(screen, "Nimi: ", 80, 30, font)
        draw_text(screen, input_text, 80, 60, font)
        update_pygame_screen()

        input_text, active = get_user_input(input_text, active, False, True)

    result = get_user_info(input_text)
    if result:
        user_id = result[0]
        user_name = result[1]
        wipe_pygame_screen(screen)
        draw_text(screen, f"Käyttäjä {user_name} kirjautunut sisään", 80, 30, font)
        update_pygame_screen()
        time.sleep(2)


def add_new_user(screen, font):
    active = True
    while active:
        wipe_pygame_screen(screen)
        draw_text(screen, "ESC", 5, 5, font)
        new_user_name, active = get_text_input(screen, font, "Nimi: ", False, True)
        update_pygame_screen()

        result = check_if_name_in_db(new_user_name)
        if result:
            wipe_pygame_screen(screen)
            draw_text(screen, f"Käyttäjä {new_user_name} löytyy jo tietokannasta", 80, 30, font)
            update_pygame_screen()
            time.sleep(2)
        else:
            if new_user_name:
                print(f"Active status: ", active)
                wipe_pygame_screen(screen)
                #add_user_to_db(new_user_name, fuel_capacity)
                draw_text(screen, f"Käyttäjä {new_user_name} lisätty tietokantaan", 80, 30, font)
                update_pygame_screen()
                time.sleep(2)
    wipe_pygame_screen(screen)

def logged_in_user_text(screen, font):
    global user_id, user_name
    result = check_if_logged_in()
    if result:
        user_id = result[0]
        user_name = result[1]
    if user_id != "" and user_name != "":
        draw_text(screen, f"{user_name}", 10, 10, font)