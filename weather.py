import random
def generate_random_weather():
    weather_conditions = ["Clear", "Cloudy", "Rain", "Storm", "Snow"]
    weather = random.choice(weather_conditions)
    wind_speed = random.uniform(0, 25)
    return {"weather": weather, "wind": wind_speed}