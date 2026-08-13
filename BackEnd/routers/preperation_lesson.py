from fastapi import APIRouter , Form , UploadFile , File
from models import PreperationLesson
from database import add_preperation_lesson, update_preperation_lesson, delete_preperation_lesson, search_preperation_lesson , prepare_lesson_content

router = APIRouter()

@router.get("/search")
def search_lesson(data:dict):
    return search_preperation_lesson(user_id=data["user_id"],lesson_name=data["title"])

@router.post("/")
def create(preperation_lesson: PreperationLesson):
    data = preperation_lesson.model_dump()
    preperation_lesson_id = add_preperation_lesson(data)
    return {"id": str(preperation_lesson_id)}

@router.put("/{lesson_id}")
def update(lesson_id: str, data: dict):
    data["id"] = lesson_id 
    update_preperation_lesson(data)
    return {"details": "Preparation lesson updated successfully"}

@router.delete("/{lesson_id}")
def delete(lesson_id: str):
    delete_preperation_lesson(lesson_id)
    return {"details": "Preparation lesson deleted successfully"}


@router.get("/generatePreperation")

def pdf(data:str = Form(...),pdf:UploadFile = File(...)):
    return prepare_lesson_content(grade_level=data,lesson_pdf=pdf)