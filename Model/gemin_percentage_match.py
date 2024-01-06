import os
import re
import json
import PyPDF2
from docx import Document
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv('../Config/api_key.env')

# load api key
API_KEY = os.getenv("gemini_key")
genai.configure(api_key=API_KEY)


# Function to load OpenAI model and get respones
model = genai.GenerativeModel('gemini-pro')
chat = model.start_chat(history=[])


def extract_text_from_pdf(pdf_path):
    # Initialize a PDF file reader using PdfReader
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)

        # Initialize a variable to store extracted text
        extracted_text = ""

        # Iterate through each page and extract text
        for page in reader.pages:
            extracted_text += page.extract_text()

        return extracted_text


def extract_text_from_docx(docx_path):
    try:
        # Open the DOCX file
        document = Document(docx_path)

        # Initialize an empty list to store paragraphs
        paragraphs = []

        # Iterate through each paragraph in the document
        for para in document.paragraphs:
            paragraphs.append(para.text)

        # Combine all paragraphs into a single string
        extracted_text = '\n'.join(paragraphs)

        return extracted_text
    except Exception as e:
        return f"An error occurred: {e}"


def extract_text(file_path):
    # Determine the file extension
    _, file_extension = os.path.splitext(file_path)

    # Call the appropriate extraction function based on the file extension
    if file_extension.lower() == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension.lower() == '.docx':
        return extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file type")


def query_gemini_model_resume_jd(resume_text, job_description_text):
    # question = f"How relevant is this resume: {resume_text} to this job description: {job_description_text}?"
    question = f"Analyze the relevance of this resume to the given job description and provide a response as a " \
               f"percentage match. Resume: {resume_text}. Job Description: {job_description_text}."
    try:
        # Send the question to the GEMIN model and receive the response
        response = chat.send_message(question, stream=True)

        # Process the streamed response
        full_response = ""
        for part in response:
            full_response += part.text
        return full_response

    except Exception as e:
        print(f"An error occurred while querying the GEMINI model: {e}")
        return None


def extract_years_experience_name(input_text):
    # Split the text into lines
    lines = input_text.strip().split('\n')

    # Initialize variables
    name = None
    skills = None
    experience = None

    # Iterate through each line and extract information
    for line in lines:
        if ' = ' in line:  # Check if the separator is in the line
            key, value = line.split(' = ', 1)
            if key == 'Name':
                name = value
            elif key == 'Skills':
                skills = value
            elif key == 'Experience':
                experience = value

    ## Now the information is stored in variables
    # print("Name:", name)
    # print("Skills:", skills)
    # print("Experience:", experience)
    return name, skills, experience


def query_gemini_model(text):
    # question = f"How relevant is this resume: {resume_text} to this job description: {job_description_text}?"
    question = f"""Please analyze the following text and extract the following details:
                    1. Name of the candidate.
                    2. List of skills, with a focus on programming languages and technologies.
                    3. Total years of experience.
    Resume Text: {text}
    Please provide output in below format
    output format:
    Name = provided name if any
    Skills = first_skill, second_skill
    Experience = years of experience if any
    """
    try:
        # Send the question to the GEMIN model and receive the response
        response = chat.send_message(question, stream=True)

        # Process the streamed response
        full_response = ""
        for part in response:
            full_response += part.text
        return full_response

    except Exception as e:
        print(f"An error occurred while querying the GEMINI model: {e}")
        return None

# def interpret_response_and_get_percentage(response):
#     match_keywords = {
#         "highly relevant": 90,  # Assuming this phrase means a very high match
#         "very relevant": 80,
#         "moderately relevant": 60,
#         "somewhat relevant": 40,
#         "not very relevant": 20,
#         "not relevant": 10,
#         "irrelevant": 0,
#     }
#
#     # Default match percentage if no keywords are found
#     default_match_percentage = 0
#
#     # Normalize the response for easier keyword matching
#     normalized_response = response.lower()
#
#     # Check for each keyword in the response
#     for keyword, percentage in match_keywords.items():
#         if keyword in normalized_response:
#             return percentage
#
#     # Return default percentage if no keywords are found
#     return default_match_percentage


def extract_percentage(text):
    prompt = f"Read the following text and provide the percentage match mentioned:\n{text} " \
             f"the response should return as an integer value"
    try:
        # Send the question to the GEMIN model and receive the response
        response = chat.send_message(prompt, stream=True)
        full_response = ""
        for part in response:
            full_response += part.text
        return full_response

    except Exception as e:
        print(f"An error occurred while querying the GEMIN model: {e}")
        return None


def main(resume, job_description):
    # resume_path = '../Data/DibyaranjanDE.pdf'
    resume_text = extract_text(resume)

    # Query the GEMINI model
    ai_response = query_gemini_model_resume_jd(resume_text, job_description)
    match_percentage = extract_percentage(ai_response)
    return match_percentage


