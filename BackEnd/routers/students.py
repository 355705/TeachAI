from fastapi import APIRouter
from database import get_students , add_student , update_student , delete_student , search_about_students
from models import Student
router = APIRouter()

@router.get("/")
def students(data:dict):
    return get_students(data["user_id"] , data["indexPage"])

@router.post("/")
def create_student(student: Student):
    data = student.model_dump()
    return add_student(data)

@router.put("/")
def updated_student(data:dict):
    result = update_student(data)
    if(result == 0):
        return {"details": "Student not found"}
    
    return {"details": "Student updated successfully"}

@router.delete("/")
def deleted_student(data:dict):   

    delete_student(data["id"])
    return {"details": "Student deleted successfully"}

@router.get("/search")
def search_student(data:dict):
    return search_about_students(user_id=data["user_id"],student_name=data["name"])