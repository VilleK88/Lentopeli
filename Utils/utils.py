from geopy.distance import geodesic
from Database.db import get_airport_coords
import pygame
import time

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

# Määrittää pygame-ikkunan koon
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
    active = True
    while active:
        icao = get_icao_input(screen, font, prompt, True)
        airport = get_airport_coords(icao)
        if airport:
            return airport

        draw_text(screen, f"Virhe: ICAO-koodia '{icao}' ei löytynyt.", 20, 150, font)
        pygame.display.flip()

# Piirtää kirjaimia
def draw_text(screen, text, x, y, font):
    rendered_text = font.render(text, True, (255, 255, 255))
    screen.blit(rendered_text, (x, y))

# Piirtää kirjaimia keskelle näyttöä x-akselilla
def draw_text_to_center_x(screen, text, y, font):
    width, _ = get_pygame_screen_size(screen)
    rendered_text = font.render(text, True, (255, 255, 255))
    text_rect = rendered_text.get_rect(center=(width // 2, y))

    screen.blit(rendered_text, text_rect)

# Piirtää käyttäjälistan
def draw_user_list(screen, font, data_list):
    wipe_pygame_screen(screen)
    screen_width, screen_height = get_pygame_screen_size(screen)

    column_spacing = 250
    row_spacing = 40
    table_width = column_spacing * 2

    table_x = (screen_width - table_width) // 2
    name_x = table_x
    id_x = name_x + column_spacing

    header_y = (screen_height // 2) - (len(data_list) * row_spacing) / 2 - 40
    start_y = header_y + row_spacing
    line_color = (200, 200, 200)

    screen.blit(font.render("ESC", True, (255, 255, 255)), (5, 5))
    screen.blit(font.render("Nimi", True, (255, 255, 255)), (name_x, header_y))
    screen.blit(font.render("ID", True, (255, 255, 255)), (id_x, header_y))

    pygame.draw.line(screen, line_color, (name_x, header_y + 30), (name_x + table_width, header_y + 30), 2)

    y = start_y
    for row in data_list:
        id_text = str(row[0])[:8]
        name_text = font.render(row[1], True, (255, 255, 255))
        id_text_rendered = font.render(id_text, True, (255, 255, 255))

        screen.blit(name_text, (name_x, y))
        screen.blit(id_text_rendered, (id_x, y))

        pygame.draw.line(screen, line_color, (name_x, y + 30), (name_x + table_width, y + 30), 1)
        y += row_spacing

    update_pygame_screen()
    while True:
        char = press_button(pygame.K_ESCAPE)
        if char == pygame.K_ESCAPE:
            break

# Piirtää saavuit lentoasemalle tekstin
def draw_arrived_airport(airport, icao, screen, y, font):
    time.sleep(1)
    wipe_pygame_screen(screen)
    update_pygame_screen()

    width, _ = get_pygame_screen_size(screen)
    airport_str = str(airport)
    icao_str = str(icao)
    rendered_text = font.render(f"Saavuit {airport_str} {icao_str} lentokentälle.", True, (255, 255, 255))
    text_rect = rendered_text.get_rect(center=(width // 2, y))

    screen.blit(rendered_text, text_rect)
    pygame.display.update()
    time.sleep(4)

# Ottaa käyttäjän ICAO-koodin vastaan
def get_icao_input(screen, font, prompt, upper):
    input_text = ""
    active = True

    while active:
        wipe_pygame_screen(screen)
        draw_text_to_center_x(screen, prompt, 150, font)
        draw_text_to_center_x(screen, input_text, 180, font)
        update_pygame_screen()

        input_text, active = get_user_input(input_text, active, upper, False)

    return input_text.strip()

# Palauttaa käyttäjän syöttään 'enter' painalluksen jälkeen
def get_user_input(input_text, active, upper, if_esc):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                active = False
            elif event.key == pygame.K_ESCAPE and if_esc:
                active = False
            elif event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
            else:
                if upper:
                    input_text += event.unicode.upper()
                else:
                    input_text += event.unicode.lower()

    return input_text, active

# Palauttaa käyttäjän syötteen suoraan ilman 'enter' painallusta, jos se löytyy vastaanotetulta listalta
def press_button_list(key_list):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.KEYDOWN:
            if event.key in key_list:
                return event.key

    return None

# Ottaa yksittäisen käyttäjän näppäimen syötteen vastaan
def press_button(button):
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == button:
                return event.key

    return None

# Piirtää listan keskelle pygame-ruutua
def draw_centered_list(screen, font, y_start, list):
    screen_width, screen_height = get_pygame_screen_size(screen)
    y_offset = 50
    max_width = max(font.size(item)[0] for item in list)
    for i, item in enumerate(list):
        text_surface = font.render(item, True, (255, 255, 255))
        text_x = (screen_width - max_width) // 2
        text_y = y_start + i * y_offset
        screen.blit(text_surface, (text_x, text_y))
