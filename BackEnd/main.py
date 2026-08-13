from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.schedules import router as schedules_router
from routers.users import router as users_router
from routers.notes import router as notes_router
from routers.students import router as students_router
from routers.evaluations import router as evaluations_router
from routers.videos import router as videos_router
from routers.preperation_lesson import router as preperation_lesson_router
from routers.results import router as results_router
from routers.evaluations import router as evaluations_router

import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(schedules_router, prefix="/schedules", tags=["Schedules"])
app.include_router(notes_router, prefix="/notes", tags=["Notes"])
app.include_router(students_router , prefix="/students", tags=["Students"])
app.include_router(preperation_lesson_router, prefix="/preperation_lesson", tags=["Preparation Lessons"])
app.include_router(results_router, prefix="/results", tags=["Results"])
app.include_router(videos_router, prefix="/videos", tags=["Videos"])
app.include_router(evaluations_router,prefix="/evaluations", tags=["Evaluations"])

if(__name__ == "__main__"):
    uvicorn.run("main:app",host="0.0.0.0",port=8000)
