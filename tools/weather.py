def normalize_weather(temperature_c, rain=False):
    return {
        "temperature_c": float(temperature_c),
        "rain": bool(rain),
    }
