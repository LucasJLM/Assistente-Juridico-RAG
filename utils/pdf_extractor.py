import os
import zipfile
import boto3
from langchain_community.document_loaders import PyPDFLoader
from utils.log import get_logger

logger = get_logger()

def download_and_extract_documents(bucket_name, s3_key, local_zip_path="/tmp/juridicos.zip", extract_path="/tmp/extracted"):
    os.makedirs(extract_path, exist_ok=True)

    s3_client = boto3.client("s3")
    s3_client.download_file(bucket_name, s3_key, local_zip_path)
    
    with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    
    document_texts = []
    
    for root, _, files in os.walk(extract_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_path = os.path.join(root, file)
                try:
                    loader = PyPDFLoader(pdf_path)
                    documents = loader.load()
                    document_texts.extend([doc.page_content for doc in documents])
                    logger.info(f"Processado: {file}")
                except Exception as e:
                    logger.error(f"Erro ao processar {pdf_path}: {e}")
    return document_texts
