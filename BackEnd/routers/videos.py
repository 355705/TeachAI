from fastapi import APIRouter
from database import get_recommended_videos , get_all_videos



router = APIRouter()

# run pagantion of page
@router.get("/RecommendedVideos")
def recommendedVideos(data:dict):
    return get_recommended_videos(data["user_id"] , data["indexPage"])

# run pagantion of page

@router.get("/AllVideos")
def allVideos(data:dict):
    return get_all_videos(data["indexPage"])