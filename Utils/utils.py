from geopy.distance import geodesic
from Database.db import get_airport_coords
import pygame

# Alustaa pygame ikkunan pelin alussa
def initialize_pygame_screen():
    pygame.init()
    screen = pygame.display.set_mode((600, 400))
    pygame.display.set_caption("Lentopeli")
    font = pygame.font.Font(None, 30)
    return screen, font

# Laskee lentokenttien välisen etäisyyden ICAO-koodien perusteella
def calculate_distance_between_airports(icao1, icao2):
    koord1 = icao1[2], icao1[3]
    koord2 = icao2[2], icao2[3]
    return geodesic(koord1, koord2).kilometers

# Laskee etäisyyden sen hetkisen sijainnin ja määränpään välillä
def calculate_distance(current_location, icao2):
    koord1 = current_location[0], current_location[1]
    koord2 = icao2[2], icao2[3]
    return geodesic(koord1, koord2).kilometers

# Tarkistaa löytyykö syötetty ICAO-koodi tietokannasta
def get_valid_icao(screen, font, prompt):
    while True:
        icao = get_text_input(screen, font, prompt).strip().upper()
        airport = get_airport_coords(icao)
        if airport:
            return airport

        draw_text(screen, f"Virhe: ICAO-koodia '{icao}' ei löytynyt.", 20, 150, font)
        pygame.display.flip()

# Piirtää kirjaimia
def draw_text(screen, text, x, y, font):
    rendered_text = font.render(text, True, (255, 255, 255))
    screen.blit(rendered_text, (x, y))

# Piirtää käyttäjä listan User menuun
def draw_user_list(screen, font, data_list):
    header = font.render("ID    Nimi", True, (255, 255, 255))
    screen.blit(header, (380, 30))

    y_offset = 60
    for row in data_list:
        text = font.render(f"{row[0]:<5} {row[1]}", True, (255, 255, 255))
        screen.blit(text, (380, y_offset))
        y_offset += 30

# Piirtää saavuit lentoasemalle tekstin
def draw_arrived_airport(airport, icao, screen, x, y, font):
    screen.fill((0, 0, 0))
    pygame.display.flip()
    airport_str = str(airport)
    icao_str = str(icao)
    rendered_text = font.render(f"Saavuit {airport_str} {icao_str} lentokentälle.", True, (255, 255, 255))
    screen.blit(rendered_text, (x, y))
    pygame.display.update()

# Ottaa käyttäjän merkkijono syötteen vastaan
def get_text_input(screen, font, prompt):
    input_text = ""
    active = True

    while active:
        screen.fill((0, 0, 0))
        draw_text(screen, prompt, 20, 50, font)
        draw_text(screen, input_text, 20, 100, font)
        pygame.display.flip()

        input_text, active = get_user_input(input_text, active)

    return input_text.strip()

# Palauttaa käyttäjän syöttään enter painalluksen jälkeen
def get_user_input(input_text, active):
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
    return input_text, active

# Palauttaa käyttäjän syötteen suoraan
def get_press_button(key_list):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.KEYDOWN:
            if event.key in key_list:
                return event.key

    return None