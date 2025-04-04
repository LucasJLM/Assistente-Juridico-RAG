import os
import json
import boto3
import asyncio
from utils.pdf_extractor import download_and_extract_documents
from utils.embeddings_generator import generate_and_index_embeddings
from utils.log import get_logger

logger = get_logger()

# Variáveis de ambiente
BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
DOCUMENTS_KEY = os.environ.get("S3_DOCUMENTS_KEY", "juridicos.zip")
EMBEDDINGS_KEY = os.environ.get("S3_EMBEDDINGS_KEY", "embeddings.json")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

logger.info("Inicializando Lambda function...")

def perform_indexation():
    """
    Executa a indexação:
      - Extrai os textos dos PDFs contidos no arquivo compactado 'juridicos.zip' do bucket, onde é descompactado.
      - Gera embeddings e armazena os dados no ChromaDB,
      - Exporta o índice (JSON compactado em tar.gz) para o S3.
    """
    logger.info("Iniciando o processo de indexação...")
    
    try:
        texts = download_and_extract_documents(BUCKET_NAME, DOCUMENTS_KEY)
        logger.info(f"Extraídos {len(texts)} páginas de texto com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao extrair documentos: {str(e)}")
        raise
    
    try:
        bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")
    except Exception as e:
        logger.error(f"Erro ao inicializar o cliente do Bedrock: {str(e)}")
        raise
    
    try:
        embeddings_collection = generate_and_index_embeddings(texts, BUCKET_NAME)
        logger.info("Embeddings gerados e indexados com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao gerar e indexar embeddings: {str(e)}")
        raise
    
    result = {
        "status": "success",
        "total_documents": len(texts),
        "message": "Embeddings foram gerados e o índice exportado com sucesso"
    }
    logger.info("Indexação concluída com sucesso.")
    return result

def lambda_handler(event, context):
    """
    Handler principal do Lambda.
    Executa a indexação, perform_indexation().
    """
    logger.info("Lambda handler acionado.")
    
    try: 
        result = perform_indexation()
        logger.info("Processo concluído com sucesso. Retornando resposta HTTP 200.")
        return {
            "statusCode": 200, 
            "body": json.dumps(result)
        }
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
        return {
            "statusCode": 500, 
            "body": json.dumps({"erro": str(e)})
        }
