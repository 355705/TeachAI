from pydantic import BaseModel

class User(BaseModel):
    nameAr: str
    nameEn: str
    email: str
    password:str
    nationalID:str
    subject: str
    academicLevel:list
    isAdmin:bool
    role: str
    premium:bool = False

class UserWithID(BaseModel):
    id:str
    nameAr:str
    nameEn:str
    email:str
    password:str
    nationalID:str
    subject: str
    academicLevel:list
    isAdmin:bool
    role:str

class Schedule(BaseModel):
    user_id: str
    name: str
    startAt: str
    endAt: str
    day: str
    color: str
    weekOffset: int = 0

class Notes(BaseModel):
    user_id: str
    title: str
    content: str
    category: str = "General"
    color: str = "cyan"
    
class Student(BaseModel):
    user_id: str
    name: str
    strength :str
    weakness:str
    className: str
    academicLevel: str
    status: str = "Stable"

class ExamResult(BaseModel):
    user_id: str
    exam_title: str
    score: float
    is_passed: bool
    blooms_level: str  # "Remembering", "Understanding", "Applying", "Analyzing"

class PreperationLesson(BaseModel):
    user_id: str
    title: str
    content: str
    academicLevel: str
    chapter: str
    isFirstTerm: bool
    mode: str = "Manual"
    objectives: str = ""
    outline: str = ""
    homework: str = ""
    date: str = ""

