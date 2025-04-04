import os
import json
import boto3
import tarfile
import chromadb
from langchain_aws import BedrockLLM
from langchain_community.embeddings import BedrockEmbeddings
from langchain.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from utils.log import get_logger

logger = get_logger()

BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
INDEX_FOLDER = "chroma_index"

# Classe customizada para adicionar o método embed_query
class CustomBedrockEmbeddings(BedrockEmbeddings):
    def embed_query(self, text: str):
        return self.embed_documents([text])[0]

def load_index_from_s3(bucket_name=BUCKET_NAME, index_folder=INDEX_FOLDER):
    """
    Baixa o índice (tar.gz) do S3, extrai e lê o arquivo index.json.
    Retorna os dados do índice e o caminho temporário.
    """
    tmp_index_path = "/tmp/chroma_index"
    tar_file = f"{tmp_index_path}.tar.gz"
    os.makedirs(tmp_index_path, exist_ok=True)
    s3_client = boto3.client("s3")
    s3_key = f"{index_folder}/index.tar.gz"
    logger.info(f"Baixando índice do S3: {bucket_name}/{s3_key}")
    s3_client.download_file(bucket_name, s3_key, tar_file)
    logger.info("Índice baixado com sucesso")
    with tarfile.open(tar_file, "r:gz") as tar:
        tar.extractall(path=tmp_index_path)
    index_json_path = os.path.join(tmp_index_path, "index.json")
    with open(index_json_path, "r") as f:
        collection_data = json.load(f)
    return collection_data, tmp_index_path

def setup_rag():
    """
    Configura o vectorstore e a chain RAG a partir do índice extraído do S3.
    Retorna uma função que, dada uma consulta, gera a resposta..
    """
    bedrock_client = boto3.client("bedrock-runtime", region_name="us-east-1")
    embeddings = CustomBedrockEmbeddings(client=bedrock_client, model_id="amazon.titan-embed-text-v2:0")
    collection_data, tmp_index_path = load_index_from_s3()
    chroma_client = chromadb.Client()
    collection_name = "legal_docs"
    try:
        chroma_client.delete_collection(name=collection_name)
    except Exception:
        pass
    collection = chroma_client.create_collection(name=collection_name)
    collection.add(
        ids=collection_data["ids"],
        metadatas=collection_data.get("metadatas"),
        documents=[str(doc) for doc in collection_data["documents"]],
        embeddings=collection_data["embeddings"]
    )
    logger.info("Coleção Chroma preenchida com sucesso")
    vectorstore = Chroma(client=chroma_client, collection_name=collection_name, embedding_function=embeddings)
    llm = BedrockLLM(client=bedrock_client, model_id="amazon.titan-text-express-v1", model_kwargs={"temperature": 0.7})
    prompt_template = PromptTemplate(
        input_variables=["context", "question"],
        template="Com base no seguinte contexto:\n\n{context}\n\nResponda à pergunta: {question}"
    )
    def perform_query(question):
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        relevant_docs = retriever.get_relevant_documents(question)
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        logger.info(f"Recuperados {len(relevant_docs)} documentos relevantes")
        prompt = prompt_template.format(context=context, question=question)
        response = llm.predict(prompt)
        return response
    return perform_query