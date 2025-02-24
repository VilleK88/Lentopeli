import random
from dotenv import load_dotenv
def generate_random_weather():
    weather_conditions = ["Selkeää", "Pilvistä", "Sateista", "Myrsky", "Lumisadetta"]
    weather = random.choice(weather_conditions)
    wind_speed = random.uniform(0, 25)
    return {"weather": weather, "wind": wind_speed}