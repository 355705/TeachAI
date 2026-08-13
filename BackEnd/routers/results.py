from fastapi import APIRouter, HTTPException
from models import ExamResult
from database import get_user_results
from datetime import datetime

router = APIRouter()

@router.get("/dashboard/{user_id}")
def get_teacher_dashboard_stats(user_id: str):
    results = get_user_results(user_id)
    
    total_exams = len(results)
    
    if total_exams == 0:
        return {
            "top_cards": {
                "average_score": 0, "pass_rate": 0, 
                "passed_count": 0, "total_exams": 0, 
                "competency_level": "NO DATA"
            },
            "blooms_mastery": {},
            "evaluation_log": []
        }

    total_score = sum(r.get("score", 0) for r in results)
    average_score = round(total_score / total_exams, 1)
    
    passed_exams = [r for r in results if r.get("is_passed")]
    passed_count = len(passed_exams)
    pass_rate = round((passed_count / total_exams) * 100, 1)

    competency_level = "NEEDS IMPROVEMENT"
    if average_score >= 80:
        competency_level = "PROFICIENT"
    elif average_score >= 60:
        competency_level = "COMPETENT"

    blooms_stats = {}
    for r in results:
        level = r.get("blooms_level", "Unknown")
        if level not in blooms_stats:
            blooms_stats[level] = {"total_score": 0, "count": 0}
        
        blooms_stats[level]["total_score"] += r.get("score", 0)
        blooms_stats[level]["count"] += 1

    blooms_mastery = {}
    for level, stats in blooms_stats.items():
        blooms_mastery[level] = round(stats["total_score"] / stats["count"], 1)

    evaluation_log = []
    
    for r in reversed(results): 
        evaluation_log.append({
            "exam_title": r.get("exam_title"),
            "score": r.get("score"),
            "blooms_level": r.get("blooms_level"),
            "date_taken": r.get("date_taken"),
            "is_passed": r.get("is_passed")
        })

    return {
        "top_cards": {
            "average_score": average_score,
            "pass_rate": pass_rate,
            "passed_count": passed_count,
            "total_exams": total_exams,
            "competency_level": competency_level
        },
        "blooms_mastery": blooms_mastery,
        "evaluation_log": evaluation_log
    }