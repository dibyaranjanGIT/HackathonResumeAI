import os
import google.generativeai as genai

from dotenv import load_dotenv
load_dotenv('../Config/api_key.env')


API_KEY = os.getenv("gemini_key")
genai.configure(api_key=API_KEY)

## Function to load OpenAI model and get respones
model = genai.GenerativeModel('gemini-pro')
chat = model.start_chat(history=[])

# print("*******")
# print(API_KEY)


def get_gemini_response(question):
    try:
        response_text = chat.send_message(question, stream=True)
        full_response = ""
        for part in response_text:  # Iterate over streamed response
            full_response += part.text  # Accumulate the response parts
        return full_response
    except Exception as e:
        print(f"An error occurred: {e}")
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

    # Now the information is stored in variables
    print("Name:", name)
    print("Skills:", skills)
    print("Experience:", experience)


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

# question = "tell me a who is prime minister of india"
# response = get_gemini_response(question=question)
# if response:
#     print(response)  # or the appropriate attribute for the text response
# else:
#     print("No response received or an error occurred.")


text = "Python developer having 6 years of experience"
print(query_gemini_model(text))
print("***************")
content = query_gemini_model(text)
extract_years_experience_name(content)