from fastapi import APIRouter
from models import Schedule
from database import get_schedule, add_schedule, delete_schedule

router = APIRouter()

# GET
@router.get("/")
def get(user_id: str):
        user_schedule = get_schedule(user_id)
        return {"data": user_schedule}

# CREATE
@router.post("/")
def create(schedule: Schedule):
        data = schedule.model_dump()
        schedule_id = add_schedule(data)
        return {"id": str(schedule_id)}

# DELETE
@router.delete("/")
def delete(data:dict):
        delete_schedule(data["id"])
        return {"details": "Schedule deleted successfully"}
