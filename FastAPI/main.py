import sys
import shutil
from pathlib import Path
from pymongo import MongoClient
from bson import ObjectId, errors
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, Request, APIRouter, Query
from fastapi.responses import HTMLResponse, JSONResponse

# Get the parent directory of the current script's directory
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from Model import llm_langchain_qa

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
user_router = APIRouter()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Replace with your MongoDB Atlas connection string
CONNECTION_STRING = "mongodb+srv://dibyamongo:rLtI8oJmCCo6I34m@dibya.d7hfomy.mongodb.net/"

# PyMongo setup
client = MongoClient(CONNECTION_STRING)
db = client.dibya
collection = db.resume_data


# Root function
@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload/")
async def upload_file(request: Request, file: UploadFile = File(...)):
    print(file)
    # Here you can handle the uploaded file
    file_location = f"../Data/{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    llm_langchain_qa.main(file_location) # Here calling the LLM function
    return templates.TemplateResponse("upload.html", {"request": request})


# Function to fetch all users
def fetch_all_users():
    users = list(collection.find({}))
    for user in users:
        user["_id"] = str(user["_id"])  # Convert ObjectId to string
    return users

# New route to get all users
@user_router.get("/users")
def get_all_users():
    users = fetch_all_users()
    return users

# Function to fetch all users by name
async def search_name_in_database(name_query: str):
    # MongoDB query using a regex for case-insensitive search
    query = {"name": {"$regex": name_query, "$options": "i"}}
    results = collection.find(query, {"_id": 0, "name": 1, "experience": 1, "skill_set": 1})

    # Convert the results to a list of dictionaries
    return list(results)

# Route to search user by name
@app.get("/search/name")
async def search_items(name_query: str = Query(None, min_length=3)):
    results = await search_name_in_database(name_query)
    return results


# Function to fetch all users by experience
def search_experience_in_database(experience_query: str):
    # MongoDB query using a regex for case-insensitive search on the experience field
    experience_query = str(experience_query)
    query = {"experience": {"$regex": experience_query, "$options": "i"}}
    results = collection.find(query, {"_id": 0, "name": 1, "experience": 1, "skill_set": 1})

    # Convert the results to a list of dictionaries
    return list(results)


# Route to search user by experience
@app.get("/search/experience")
def search_by_experience(experience_query: str = Query(None, min_length=1)):
    results = search_experience_in_database(experience_query)
    return results


# Function to fetch all users by experience
def search_skillset_in_database(skillset_query: str):
    # MongoDB query using a regex for case-insensitive search on the experience field
    skillset_query = str(skillset_query)
    query = {"skill_set": {"$regex": skillset_query, "$options": "i"}}
    results = collection.find(query, {"_id": 0, "name": 1, "experience": 1, "skill_set": 1})

    # Convert the results to a list of dictionaries
    return list(results)


# Route to search user by skill set
@app.get("/search/skillset")
def search_by_experience(skillset_query: str = Query(None, min_length=3)):
    results = search_skillset_in_database(skillset_query)
    return results


""" 
# Function to fetch user by ObjectId
@user_router.get("/user")
async def get_user(user_id: str = Query(...)):
    try:
        object_id = ObjectId(user_id)  # Convert string to ObjectId
    except errors.InvalidId:
        return JSONResponse(status_code=400, content={"message": "Invalid user ID format"})

    user_document = collection.find_one({"_id": object_id})
    if user_document:
        # Convert ObjectId to string for JSON serialization
        user_document["_id"] = str(user_document["_id"])
        return user_document
    else:
        return JSONResponse(status_code=404, content={"message": "User not found"})
"""
app.include_router(user_router)