from fastapi import APIRouter
from app.models.schemas import SolarInput
from app.services.solar_service import calculate_solar

router = APIRouter()

@router.post("/calculate")
def solar_calc(data: SolarInput):
    return calculate_solar(data.area, data.sunlight_hours)