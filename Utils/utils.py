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

# Pyyhkii pygame-ikkunan tyhjäksi
def wipe_pygame_screen(screen):
    screen.fill((0, 0, 0))

# Päivittää pygame-ikkunan
def update_pygame_screen():
    pygame.display.flip()

def get_pygame_screen_size(screen):
    screen_width, screen_height = screen.get_size()
    return screen_width, screen_height

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
        icao = get_text_input(screen, font, prompt, True).strip().upper()
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
    wipe_pygame_screen(screen)
    screen_width, screen_height = get_pygame_screen_size(screen)
    column_spacing = 250
    y_start = 50
    y_offset = 40
    line_color = (100, 100, 100)

    total_table_width = column_spacing + 150
    table_x = (screen_width - total_table_width) // 2

    name_x = table_x
    id_x = name_x + column_spacing
    line_x_start = name_x - 20
    line_x_end = id_x + 80

    screen.blit(font.render("Nimi", True, (255, 255, 255)), (name_x, y_start))
    screen.blit(font.render("ID", True, (255, 255, 255)), (id_x, y_start))

    y = y_start + y_offset
    pygame.draw.line(screen, line_color, (line_x_start, y + 25), (line_x_end, y + 25), 1)
    for row in data_list:
        id_text = str(row[0])[:8]
        name_text = font.render(row[1], True, (255, 255, 255))
        id_text_rendered = font.render(id_text, True, (255, 255, 255))
        screen.blit(name_text, (name_x, y))
        screen.blit(id_text_rendered, (id_x, y))
        pygame.draw.line(screen, line_color, (line_x_start, y + 25), (line_x_end, y + 25), 1)
        y += y_offset

    update_pygame_screen()
    user_input = input("")

# Piirtää saavuit lentoasemalle tekstin
def draw_arrived_airport(airport, icao, screen, x, y, font):
    wipe_pygame_screen(screen)
    update_pygame_screen()
    airport_str = str(airport)
    icao_str = str(icao)
    rendered_text = font.render(f"Saavuit {airport_str} {icao_str} lentokentälle.", True, (255, 255, 255))
    screen.blit(rendered_text, (x, y))
    pygame.display.update()

# Ottaa käyttäjän syötteen vastaan
def get_text_input(screen, font, prompt, upper):
    input_text = ""
    active = True

    while active:
        wipe_pygame_screen(screen)
        draw_text(screen, prompt, 20, 50, font)
        draw_text(screen, input_text, 20, 100, font)
        update_pygame_screen()

        input_text, active = get_user_input(input_text, active, upper)

    return input_text.strip()

# Palauttaa käyttäjän syöttään enter painalluksen jälkeen
def get_user_input(input_text, active, upper):
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
                if upper:
                    input_text += event.unicode.upper()
                else:
                    input_text += event.unicode.lower()
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