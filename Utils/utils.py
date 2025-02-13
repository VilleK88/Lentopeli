from geopy.distance import geodesic
from Database.db import get_airport_coords
import pygame
def calculate_distance_between_airports(icao1, icao2):
    koord1 = icao1[2], icao1[3]
    koord2 = icao2[2], icao2[3]
    return geodesic(koord1, koord2).kilometers
def calculate_distance(current_location, icao2):
    koord1 = current_location[0], current_location[1]
    koord2 = icao2[2], icao2[3]
    return geodesic(koord1, koord2).kilometers
def get_valid_icao(screen, font, prompt):
    while True:
        icao = get_text_input(screen, font, prompt).strip().upper()
        airport = get_airport_coords(icao)
        if airport:
            return airport
        draw_text(screen, f"Virhe: ICAO-koodia '{icao}' ei löytynyt.", 20, 150, font)
        pygame.display.flip()
def draw_text(screen, text, x, y, font):
    rendered_text = font.render(text, True, (255, 255, 255))
    screen.blit(rendered_text, (x, y))

def get_text_input(screen, font, prompt):
    input_text = ""
    active = True

    while active:
        screen.fill((0, 0, 0))
        draw_text(screen, prompt, 20, 50, font)
        draw_text(screen, input_text, 20, 100, font)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    active = False
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode.upper()

    return input_text.strip()