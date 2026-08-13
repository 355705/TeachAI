from fastapi import APIRouter, BackgroundTasks, Form, UploadFile, File
from database import generate_all_questions , sessionExam , examDetails , evaulate_prepare , EvaluationDetails , sessionEvaluation
import json
router = APIRouter()

### run once
@router.post("/examSession")
def generateExamSesstion(background_tasks:BackgroundTasks,data:dict):
    exam_id = sessionExam(user_id=data["user_id"])
    background_tasks.add_task(
        generate_all_questions,
        exam_id,
        data["subject"],
        data["acadmicLevel"])
    return {"exam_id" : exam_id}


### While LOOP
@router.get("/examDetails")
def getExamDetails(data:dict):
    return examDetails(data["exam_id"])

### run once
@router.post("/evaluationSession")
def evaluationExam(backgorund_tasks:BackgroundTasks,questions_details:str = Form(...),data:str = Form(...),audios:list[UploadFile] = File(None)):
    questions_details = json.loads(questions_details)
    data = json.loads(data)
    exam_id = sessionEvaluation(user_id=data["user_id"])
    backgorund_tasks.add_task(
        evaulate_prepare,
        exam_id,
        data["subject"],
        data["acadmicLevel"],
        questions_details,
        audios)
    return {"exam_id" : exam_id}
    
### While LOOP
@router.get("/examEvaluationDetails")
def getExamEvaluationDetails(data:dict):
    return EvaluationDetails(data["exam_id"])