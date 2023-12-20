import os
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

load_dotenv('api_key.env')
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
    print(experience)

    query = "What is the name of the candidate"
    docs = document_search.similarity_search(query)
    name = chain.run(input_documents=docs, question=query)
    print(name)

    query = "What is the primary skill set of the candidate"
    docs = document_search.similarity_search(query)
    skill_set = chain.run(input_documents=docs, question=query)
    print(skill_set)

    my_dict = {
        "name": name,
        "experience": experience,
        "skill_set": skill_set
    }
    return my_dict


def upload_data_db():
    # with open('data.json', 'w') as json_file:
    #     json.dump(my_dict, json_file, indent=4)

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


if __name__ == '__main__':
    # pdf_file = '../Data/Jeeban.pdf'
    # texts = read_pdf(pdf_file)

    # my_dict = call_llm_chain()

    upload_data_db()
