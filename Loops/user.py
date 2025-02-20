from Utils.utils import draw_user_list, draw_text, get_press_button, get_user_input
import pygame
from Database.db import show_current_users, get_user_info

# User info
user_name = ""
user_id = ""
logged_in = ""

def user_menu(screen, font):
    data_list = show_current_users()
    input_text = ""
    key_list = [pygame.K_1, pygame.K_2, pygame.K_3]
    active = True

    while active:
        screen.fill((0, 0, 0))
        draw_user_list(screen, font, data_list)
        draw_text(screen, "1 - Tee uusi pelaaja", 80, 30, font)
        draw_text(screen, "2 - Valitse pelaaja", 80, 60, font)
        draw_text(screen, "3 - Aloita peli", 80, 90, font)
        draw_text(screen, input_text, 80, 120, font)
        pygame.display.flip()

        char = get_press_button(key_list)
        if char == pygame.K_2:
            select_user(screen, font)
        elif char == pygame.K_3:
            active = False

    return input_text.strip()

def select_user(screen, font):
    input_text = ""
    active = True

    while active:
        screen.fill((0, 0, 0))
        draw_text(screen, "Nimi: ", 80, 30, font)
        draw_text(screen, input_text, 80, 60, font)
        pygame.display.flip()

        input_text, active = get_user_input(input_text, active, False)
    result = get_user_info(input_text)
    if result:
        user_id = result[0]
        user_name = result[1]
        print(f"Käyttäjä: {user_name}, ID: {user_id}")

    return input_text.strip()