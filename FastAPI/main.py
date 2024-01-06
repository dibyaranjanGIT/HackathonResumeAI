import sys
import shutil
import json
import re
from pathlib import Path
from pymongo import MongoClient
from bson import ObjectId, errors
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, Request, APIRouter, Query, Form
from fastapi.responses import HTMLResponse, JSONResponse

# Get the parent directory of the current script's directory
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from Model import llm_langchain_qa
from Model import gemin_percentage_match

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


@app.post("/upload_file_jd")
async def upload_file_and_description(file: UploadFile = File(...), job_description: str = Form(...)):
    # Here you can handle the uploaded file and the job description
    # Save the file, process the text, etc.
    file_location = f"../Data/{file.filename}"
    with open(file_location, "wb") as file_object:
        shutil.copyfileobj(file.file, file_object)
    percentage_match = gemin_percentage_match.main(file_location, job_description)
    percentage_match = percentage_match.replace("%", "")

    # For example, just returning the file name and job description
    # return {"filename": file.filename, "job_description": job_description, "percentage": percentage_match}
    return {"percentage": float(percentage_match)}


# Function to fetch all users by skill set and experience
def extract_skillset_experience_name(skillset_query: str, experience_query: str, name_query: str):
    skillset_query = str(skillset_query)
    experience_query = str(experience_query)
    name_query = str(name_query)
    # MongoDB query using regex for case-insensitive search on both skill_set and experience fields
    query = {
        "$or": [
            {"skill_set": {"$regex": skillset_query, "$options": "i"}},
            {"experience": {"$regex": experience_query, "$options": "i"}},
            {"name": {"$regex": name_query, "$options": "i"}}
        ]
    }
    results = collection.find(query, {"_id": 0, "name": 1, "experience": 1, "skill_set": 1})
    # Convert the results to a list of dictionaries
    return list(results)


# Route to search user by skill set and experience
@app.get("/search/skillset-experience-name")
def search_by_skillset_experience_name(input_text: str = Query(None, min_length=1)):
    # Extract skills and experience from the input text
    processed_text = gemin_percentage_match.query_gemini_model(input_text)
    # extracted_name, extracted_skills, extracted_experience = \
    #     gemin_percentage_match.extract_years_experience_name(processed_text)

    try:
        extracted_name, extracted_skills, extracted_experience = \
        gemin_percentage_match.extract_years_experience_name(processed_text)

        # Convert extracted experience to a string for MongoDB query, if it is not None
        match = re.search(r'\d+', extracted_experience)
        extracted_experience = int(match.group()) if match else None

    except:
        extracted_experience = 0
        extracted_skills = ''
        extracted_name = ''

    print("************")
    print(extracted_skills)
    print(extracted_experience)
    print(extracted_name)

    results = extract_skillset_experience_name(extracted_skills, extracted_experience, extracted_name)
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