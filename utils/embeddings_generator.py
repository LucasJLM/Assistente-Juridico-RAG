import os
import json
import tarfile
import boto3
import chromadb
from langchain_aws import BedrockEmbeddings
from langchain.schema import Document  # Importa o objeto Document
from utils.log import get_logger

logger = get_logger()

def generate_and_index_embeddings(documents, bucket_name, index_folder='chroma_index'):
    """
    Gera embeddings para os documentos, cria uma coleção Chroma e salva os dados do índice
    (incluindo os embeddings, documentos, ids e metadatas) em um arquivo JSON. Em seguida,
    compacta o JSON em um tar.gz e faz o upload para o S3.
    
    Parâmetros:
      - documents: Lista de objetos que devem possuir os atributos 'page_content' e 'metadata'. 
                   Se for uma string, será encapsulada em um Document com metadata padrão.
      - bucket_name: Nome do bucket S3 onde o índice será salvo.
      - index_folder: Pasta no bucket onde o índice ficará (default: 'chroma_index').
    
    Retorna:
      - A coleção Chroma criada.
    """
    # Converte itens para objetos Document garantindo metadata não vazia
    docs = []
    for doc in documents:
        if isinstance(doc, str):
            docs.append(Document(page_content=doc, metadata={"source": "unknown"}))
        else:
            # Se o documento possuir metadata vazia, atribui um valor padrão
            if not doc.metadata or doc.metadata == {}:
                doc.metadata = {"source": "unknown"}
            docs.append(doc)
    
    # Extrai textos e metadados dos documentos
    texts = [doc.page_content for doc in docs]
    metadatas = [doc.metadata for doc in docs]
    ids = [f"chunk_{i}" for i in range(len(docs))]
    
    # Configura o modelo do Bedrock e os embeddings
    bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')
    embeddings = BedrockEmbeddings(
        client=bedrock_client,
        model_id="amazon.titan-embed-text-v2:0"
    )
    
    # Gera embeddings em lote
    logger.info("Gerando embeddings em lote para todos os documentos")
    try:
        document_embeddings = embeddings.embed_documents(texts)
        logger.info(f"Embeddings gerados. Tamanho: {len(document_embeddings)}")
    except Exception as e:
        logger.error(f"Erro ao gerar embeddings: {str(e)}")
        raise
    
    # Cria coleção Chroma em memória e adiciona os dados
    chroma_client = chromadb.Client()
    collection = chroma_client.create_collection(name="legal_docs")
    collection.add(
        ids=ids,
        embeddings=document_embeddings,
        metadatas=metadatas,
        documents=texts
    )
    logger.info("Coleção Chroma preenchida com sucesso")
    
    # Prepara os dados da coleção para exportação
    collection_data = {
        "ids": ids,
        "embeddings": document_embeddings,
        "metadatas": metadatas,
        "documents": texts
    }
    
    # Cria um diretório temporário para armazenar o índice
    tmp_index_path = "/tmp/chroma_index"
    os.makedirs(tmp_index_path, exist_ok=True)
    
    # Salva os dados da coleção em um arquivo JSON
    json_file = os.path.join(tmp_index_path, "index.json")
    with open(json_file, "w") as f:
        json.dump(collection_data, f)
    logger.info(f"Index JSON criado em: {json_file}")
    
    # Compacta o arquivo JSON em um tar.gz
    tar_file = f"{tmp_index_path}.tar.gz"
    with tarfile.open(tar_file, "w:gz") as tar:
        tar.add(json_file, arcname="index.json")
    logger.info(f"Tarball criado em: {tar_file}")
    
    # Faz upload do tar.gz para o S3
    s3_client = boto3.client('s3')
    s3_key = f"{index_folder}/index.tar.gz"
    s3_client.upload_file(tar_file, bucket_name, s3_key)
    logger.info(f"Índice salvo no S3 em {bucket_name}/{s3_key}")
    
    return collection