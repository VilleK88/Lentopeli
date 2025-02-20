from Utils.utils import draw_user_list, draw_text, get_user_input, get_press_button
import pygame

user_name = ""
user_id = ""
logged_in = ""

def user_menu(screen, font, data_list):
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
        if char == pygame.K_3:
            active = False

    return input_text.strip()