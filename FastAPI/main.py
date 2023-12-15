import sys
import shutil
from pathlib import Path
from pymongo import MongoClient
from bson import ObjectId, errors
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, File, UploadFile, Request, APIRouter, Query
from fastapi.responses import HTMLResponse, JSONResponse

# Get the parent directory of the current script's directory
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from Model import llm_langchain_qa

app = FastAPI()
user_router = APIRouter()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Replace with your MongoDB Atlas connection string
CONNECTION_STRING = "mongodb+srv://dibyamongo:rLtI8oJmCCo6I34m@dibya.d7hfomy.mongodb.net/"

# PyMongo setup
client = MongoClient(CONNECTION_STRING)
db = client.dibya
collection = db.resume_data


@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload/")
async def upload_file(request: Request, file: UploadFile = File(...)):
    # Here you can handle the uploaded file
    file_location = f"../Data/{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    llm_langchain_qa.main(file_location) # Here calling the LLM function
    return templates.TemplateResponse("upload.html", {"request": request})

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

app.include_router(user_router)