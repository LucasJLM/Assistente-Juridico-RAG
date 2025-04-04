import os
import json
import boto3
import requests
from utils.rag_module import setup_rag  # Importando o módulo otimizado
from utils.log import get_logger

logger = get_logger()

class JuridicoBot:
    def _init_(self):
        """Inicializa o bot com a função otimizada de consulta do RAG."""
        logger.info("🔄 Configurando RAG...")
        self.query_rag = setup_rag()  # Obtendo a função otimizada do RAG

    def query_documents(self, query):
        """Consulta os documentos via RAG e retorna a resposta."""
        logger.info(f"🔍 Consultando: {query}")
        response = self.query_rag(query)
        return response

def send_telegram_message(chat_id, text, telegram_token):
    """Envia uma mensagem para o Telegram"""
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def process_telegram_update(update, juridico_bot, telegram_token):
    """Processa uma atualização do Telegram"""
    if "message" not in update:
        return {"status": "ignored", "reason": "not a message"}
    
    message = update["message"]
    if "text" not in message:
        return {"status": "ignored", "reason": "no text in message"}
    
    chat_id = message["chat"]["id"]
    text = message["text"]
    
    if text.startswith("/start"):
        send_telegram_message(chat_id, "👋 Olá! Sou um assistente jurídico. Como posso ajudar?", telegram_token)
        return {"status": "command", "command": "start"}
    
    if text.startswith("/help"):
        help_text = "📚 Assistente Jurídico\n\nDigite sua pergunta sobre assuntos jurídicos e eu responderei."
        send_telegram_message(chat_id, help_text, telegram_token)
        return {"status": "command", "command": "help"}
    
    try:
        send_telegram_message(chat_id, "🔍 Pesquisando informações...", telegram_token)
        resposta = juridico_bot.query_documents(text)
        send_telegram_message(chat_id, f"Resposta:\n\n{resposta}", telegram_token)
        return {"status": "success", "query": text}
    except Exception as e:
        logger.error(f"Erro ao processar consulta: {e}")
        send_telegram_message(chat_id, "❌ Erro ao processar sua consulta. Tente novamente mais tarde.", telegram_token)
        return {"status": "error", "error": str(e)}

def lambda_handler(event, context):
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not telegram_token:
        return {'statusCode': 500, 'body': json.dumps({"erro": "TELEGRAM_BOT_TOKEN não configurado"})}
    
    try:
        juridico_bot = JuridicoBot()
        if event.get("httpMethod") == "POST" and "body" in event:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
            result = process_telegram_update(body, juridico_bot, telegram_token)
            return {'statusCode': 200, 'body': json.dumps(result)}
        else:
            return {'statusCode': 400, 'body': json.dumps({"erro": "Requisição não reconhecida"})}
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        return {'statusCode': 500, 'body': json.dumps({"erro": str(e)})}