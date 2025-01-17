from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/api/subscription_info")
async def subscription_info(request: Request):
    tibber = request.app.state.tibber_instance
    return {
        "power_reading": tibber.power_reading,
        "subscription_status": tibber.subscription_status,
    }
