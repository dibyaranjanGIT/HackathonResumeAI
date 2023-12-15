import os
import json
import pymongo
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
from abc import ABC, abstractmethod
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI

class AbstractDocumentReader(ABC):
    @abstractmethod
    def read(self):
        pass

class PDFDocumentReader(AbstractDocumentReader):
    def __init__(self, file_path):
        self.file_path = file_path

    def read(self):
        pdf_reader = PdfReader(self.file_path)
        raw_text = ''
        for page in pdf_reader.pages:
            content = page.extract_text()
            if content:
                raw_text += content
        return raw_text

class WordDocumentReader(AbstractDocumentReader):
    def __init__(self, file_path):
        self.file_path = file_path

    def read(self):
        doc = Document(self.file_path)
        return '\n'.join([paragraph.text for paragraph in doc.paragraphs if paragraph.text])


class LLMChain:
    def __init__(self, api_key):
        self.api_key = api_key
        self.embeddings = OpenAIEmbeddings(openai_api_key=self.api_key)

    def call_llm_chain(self, texts):
        document_search = FAISS.from_texts(texts, self.embeddings)
        chain = load_qa_chain(OpenAI(openai_api_key=self.api_key), chain_type="stuff")
        my_dict = {}
        for query in ["total experience of the candidate", "name of the candidate", "primary skill set of the candidate"]:
            docs = document_search.similarity_search(query)
            response = chain.run(input_documents=docs, question=query)
            my_dict[query] = response
        return my_dict

class DatabaseManager:
    def __init__(self, connection_string):
        self.client = pymongo.MongoClient(connection_string)

    def upload_data_db(self, data, db_name, collection_name):
        db = self.client[db_name]
        collection = db[collection_name]
        if isinstance(data, list):
            collection.insert_many(data)
        else:
            collection.insert_one(data)

class EnvironmentManager:
    def __init__(self, env_file):
        load_dotenv(env_file)

    def get_env_variable(self, key):
        return os.getenv(key)

if __name__ == '__main__':
    env_manager = EnvironmentManager('api_key.env')
    api_key = env_manager.get_env_variable('llm_key')

    pdf_reader = PDFReader('Jeeban.pdf')
    texts = pdf_reader.read_pdf()

    llm_chain = LLMChain(api_key)
    processed_data = llm_chain.call_llm_chain(texts)

    db_manager = DatabaseManager("your_connection_string_here")
    db_manager.upload_data_db(processed_data, "dibya", "resume_data")
