from fastapi import APIRouter
from models import Notes
from database import get_notes, add_notes, update_notes, delete_notes

router = APIRouter()

# GET
@router.get("/")
def get(user_id: str):
        user_notes = get_notes(user_id)
        return {"data": user_notes}

# CREATE
@router.post("/")
def create(note: Notes):
        data = note.model_dump()
        note_id = add_notes(data)
        return {"id": str(note_id)}

# UPDATE
@router.put("/")
def update(data: dict):
        update_notes(data) #### the old is note_id = update_notes(data) and this is the new don't forget
        return {"details": "Note updated successfully"}

# DELETE
@router.delete("/")
def delete(data:dict):
        delete_notes(data["id"])
        return {"details": "Note deleted successfully"}