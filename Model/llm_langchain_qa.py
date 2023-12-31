import os
import re
import json
import pymongo
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from typing_extensions import Concatenate
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI

load_dotenv('../Config/api_key.env')
API_KEY = os.getenv('llm_key')


def read_pdf(pdf_file):
    """take the pdf file and return the raw text"""
    # provide the path of  pdf file/files.
    pdfreader = PdfReader(pdf_file)


    # read text from pdf
    raw_text = ''
    for i, page in enumerate(pdfreader.pages):
        content = page.extract_text()
        if content:
            raw_text += content

    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=800,
        chunk_overlap=200,
        length_function=len,
    )
    texts = text_splitter.split_text(raw_text)
    return texts


def call_llm_chain(texts):
    """take input text from the pdf reader and return a dictionary"""
    # Download embeddings from OpenAI
    embeddings = OpenAIEmbeddings(openai_api_key=API_KEY)
    document_search = FAISS.from_texts(texts, embeddings)
    chain = load_qa_chain(OpenAI(openai_api_key=API_KEY), chain_type="stuff")

    query = "What is the total experience of the candidate"
    docs = document_search.similarity_search(query)
    experience = chain.run(input_documents=docs, question=query)
    # Extracting only the integer part
    integer_part = re.findall(r'\d+', experience)
    integer_part = integer_part[0] if integer_part else None

    query = "Directly provide the candidate's name from the resume, without any additional text."
    docs = document_search.similarity_search(query)
    input_name = chain.run(input_documents=docs, question=query)
    # name = input_name.replace("The candidate is ", "")

    query = "List only the primary skill set of the candidate, without additional explanation or context."
    docs = document_search.similarity_search(query)
    skill_set = chain.run(input_documents=docs, question=query)

    my_dict = {
        "name": input_name,
        "experience": integer_part,
        "skill_set": skill_set
    }
    return my_dict


def upload_data_db(my_dict):
    with open('data.json', 'w') as json_file:
        json.dump(my_dict, json_file, indent=4)

    # Your MongoDB Atlas connection string
    connection_string = "mongodb+srv://dibyamongo:rLtI8oJmCCo6I34m@dibya.d7hfomy.mongodb.net/"

    # Connect to your cluster
    client = pymongo.MongoClient(connection_string)

    # Select your database
    db = client["dibya"]

    # Select your collection
    collection = db["resume_data"]

    # Load your JSON data
    with open('data.json') as file:
        file_data = json.load(file)

    # Insert the data into the collection
    if isinstance(file_data, list):
        collection.insert_many(file_data)
    else:
        collection.insert_one(file_data)


def main(pdf_file):
    # pdf_file = '../Data/Uma.pdf'
    texts = read_pdf(pdf_file)
    my_dict = call_llm_chain(texts)
    upload_data_db(my_dict)


if __name__ == '__main__':
    pdf_file = '../Data/DibyaranjanDE.pdf'
    main(pdf_file)