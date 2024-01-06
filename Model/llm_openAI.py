import os
import re
import json
from dotenv import load_dotenv
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI

load_dotenv('../Config/api_key.env')
API_KEY = os.getenv('llm_key')


def call_llm_chain(texts):
    """take input text from the pdf reader and return a dictionary"""
    # Download embeddings from OpenAI
    embeddings = OpenAIEmbeddings(openai_api_key=API_KEY)
    document_search = FAISS.from_texts(texts, embeddings)
    chain = load_qa_chain(OpenAI(openai_api_key=API_KEY), chain_type="stuff")

    query = f"""Please analyze the following text and extract the following details:
                        1. Name of the candidate.
                        2. List of skills, with a focus on programming languages and technologies.
                        3. Total years of experience.
        Resume Text: {texts}
        Please provide output in below format
        output format:
        Name = 
        Skills = first_skill, second_skill
        Experience = years of experience
        """
    docs = document_search.similarity_search(query)
    response = chain.run(input_documents=docs, question=query)
    return response

text = "Give me resume of who has experience in Java and C++ having 4 years of experience"
# text = "Javascript developer having 10 years of experience Dibya"
print(call_llm_chain(text))