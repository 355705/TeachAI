from bson import ObjectId
from fastapi import APIRouter, HTTPException
from models import User, UserWithID
from database import create_user, get_user, update_user_login, update_user, users_collection, schedules_collection, notes_collection, verify_password
from datetime import datetime


router = APIRouter()

# Check email (signup)
@router.get("/checkEmail")
def checkEmail(email: str):
    exists = users_collection.find_one({"email": email}) is not None
    return {"available": not exists}

# Get user profile (dashboard)
@router.post("/profile")
def get_user_profile(data: dict):
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    user = users_collection.find_one({"email": email})
    if user:
        user["id"] = str(user["_id"])
        user.pop("_id", None)
        return user
    raise HTTPException(status_code=404, detail="User not found")

# CREATE
@router.post("/")
def create(user: User):
    if users_collection.find_one({"email": user.email}) is not None:
        return {"details": "Email is already in use"}
    if users_collection.find_one({"nationalID": user.nationalID}) is not None:
        return {"details": "National ID is already in use"}
    data = user.model_dump()
    data["dateInserted"] = str(datetime.now().date())
    user_id = create_user(data)
    return {"id": user_id}

# VERIFY PASSWORD
@router.post("/verify")
def verify_user_password(data: dict):
    user_id = data["id"]
    password = data["password"]
    if not user_id or not password:
        raise HTTPException(status_code=400, detail="Missing user ID or password")
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user and verify_password(password, user.get("password", "")):
        return {"valid": True}
    return {"valid": False}

#UPDATE FROM LOGIN
@router.put("/updatePassword")
def updatePassword(data:dict):
    modified = update_user_login(email = data["email"],password = data["password"])
    if (modified == "this is the same of old password"):
        return {"details":"this is the same of old password"}
    if modified:
        return {"details": "updated"}
    return {"details": "error"}

# Reset password
@router.post("/resetPassword")
def resetPassword(data:dict):
    if(users_collection.find_one({"email": data["email"], "nationalID": data["nationalID"]}) == None):
        return {"details":"Email or national ID is wrong"}
    return {"details":"accept"}

# LOGIN
@router.post("/account")
def read(data:dict):
    user = get_user(email=data["email"],password=data["password"])
    if user:
        user["_id"] = str(user["_id"])
        return {
            "id": user["_id"],
            "isAdmin": user["isAdmin"],
            "nameEn": user.get("nameEn", ""),
            "email": user.get("email", ""),
            "subject": user.get("subject",""),
            "academicLevel": user.get("academicLevel",[])
        }
    else:
        return {"details":"Email or password is wrong"}

# UPDATE
@router.put("/update")
def update(user:UserWithID):
    # Check if email is already in use by another user
    existing_user = users_collection.find_one({"email": user.email, "_id": {"$ne": ObjectId(user.id)}})
    if existing_user:
        return {"details": "Email is already in use"}
    data = user.model_dump()
    data["dateInserted"] = str(datetime.now().date())
    data.pop("id",None)
    modified = update_user(user.id,data)
    if modified:
        return {"status": "updated"}
    return {"details": "User not found"}

#DELETE
@router.post("/delete")
def delete_user_account(data: dict):
    user_id = data["id"]
    password = data["password"]
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    if not password:
        raise HTTPException(status_code=400, detail="Password is required")
    
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user or not verify_password(password, user.get("password", "")):
        return {"details": "Incorrect password"}
        
    users_collection.delete_one({"_id": ObjectId(user_id)})
    schedules_collection.delete_many({"user_id": user_id})
    notes_collection.delete_many({"user_id": user_id})
    return {"status": "deleted"}
