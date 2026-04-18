def calculate_solar(area: float, sunlight_hours: float):
    efficiency = 0.18
    output = area * sunlight_hours * efficiency
    return {"estimated_output": output}
