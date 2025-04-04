# 🤖 Assistente Jurídico com RAG (Retrieval-Augmented Generation)

## 👥 Equipe do Projeto

- [Victor Marinho](https://github.com/victorj-23)
- [Lucas José](https://github.com/LucasJLM)
- [Henrique Marcos](https://github.com/Henrikoso)
- [Victor Gouveia](https://github.com/Victorgcl04)

## 🔍 Visão Geral

Este projeto implementa um assistente jurídico baseado em IA que utiliza a arquitetura RAG (Retrieval-Augmented Generation) para responder perguntas sobre documentos jurídicos. O sistema é composto por uma função Lambda AWS que:

1. Processa os documentos PDF para extração de texto, a geração de embeddings e criação do indice.
2. Fornece um chatbot via Telegram que responde consultas jurídicas baseadas nos documentos indexados.

## 🏗️ Arquitetura

O projeto é composto por:

- **AWS Lambda**: Executa o processamento de documentos e o serviço de chatbot.
- **Amazon S3**: Armazena os documentos jurídicos em PDF (em formato descompactado ou compactado) os embeddings gerados e o indice.
- **Amazon Bedrock**: Fornece os modelos de embeddings (Titan Embed) e de geração de texto (Titan Text Express).
- **ChromaDB**: Banco de dados vetorial para armazenamento e consulta de embeddings.
- **API Gateway**: Integra o chatbot com a API do Telegram.
- **Telegram Bot API**: Interface de usuário para interação com o assistente jurídico.

## 🧩 Componentes Principais

### 1️⃣ lambda_function - perform_indexation (Lambda de Processamento)

Responsável pela ingestão e indexação de documentos:
- Baixa arquivos PDF descompactados do S3.
- Extrai e processa os PDFs utilizando o `PyPDFLoader`.
- Gera embeddings usando o modelo Titan Embed da Amazon Bedrock.
- Gera o índice a ser salvo no S3.
- Armazena os embeddings no ChromaDB e exporta o índice para o S3.

### 2️⃣ telegram_bot - JuridicoBot (Chatbot)

Gerencia a interação com os usuários e a consulta de documentos:
- Carrega os embeddings e o indice do S3 importando o modulo **rag_module.py**.
- Realiza busca semântica nos documentos indexados.
- Gera respostas utilizando o modelo Titan Text Express da Amazon Bedrock.
- Integra-se com o Telegram para fornecer uma interface de chat.

## ⚙️ Configuração e Requisitos

### 🔑 Variáveis de Ambiente

- `S3_BUCKET_NAME`: Nome do bucket S3 para armazenamento de documentos e embeddings.
- `S3_DOCUMENTS_KEY`: Caminho do arquivo ZIP (ou prefixo da pasta) contendo os PDFs.
- `S3_EMBEDDINGS_KEY`: Caminho onde o índice (embeddings) será salvo (por exemplo, `embeddings.json` ou `chroma_index/index.tar.gz`).
- `TELEGRAM_BOT_TOKEN`: Token do bot do Telegram para integração.

### 📦 Dependências

- boto3
- chromadb
- langchain_community
- langchain
- langchain_aws
- logging (padrão do Python)
- requests
- zipfile (padrão do Python)
- PyPDFLoader (via langchain_community)

## 🔄 Fluxo de Funcionamento

### 📄 Processamento de Documentos

1. Os arquivos PDF são armazenados em zip (compactados) e salvos no bucket S3.
2. A função Lambda de indexação (`perform_indexation`) é acionada para processamento.
3. Os PDFs são extraídos, analisados, convertidos em embeddings e é criado o indice.
4. Os embeddings são armazenados no ChromaDB e exportados para o S3 (por exemplo, em um arquivo compactado `index.tar.gz`).

### 💬 Consulta de Documentos

1. O usuário envia uma mensagem ao bot do Telegram.
2. A API Gateway aciona a função Lambda do chatbot.
3. A consulta do usuário é convertida em embedding e comparada com os documentos indexados.
4. Os documentos mais relevantes são recuperados e usados como contexto.
5. O modelo Titan Text Express gera uma resposta baseada no contexto.
6. A resposta é sintetizada e enviada de volta ao usuário via Telegram.

## 🚀 Recursos Adicionais

### 🗄️ Cache de Consultas

O sistema implementa um cache de consultas para:
- Garantir consistência nas respostas para perguntas semelhantes.
- Reduzir a latência para consultas repetidas.
- Otimizar o uso dos recursos da AWS.

### 🔎 Refinamento de Resposta

As respostas passam por um processo de refinamento em duas etapas:
1. Geração de resposta inicial com base nos documentos recuperados.
2. Síntese final para garantir consistência e relevância.

## 🤝 Comandos do Bot

- `/start`: Inicia a interação com o bot.
- `/help`: Exibe informações de ajuda sobre como usar o bot.

## 📲 Implantação

### 1. Criar um Bucket S3 e Carregar os Documentos
- **Criação do Bucket:**  
  Crie um bucket S3 na sua conta AWS (por exemplo, `nome-do-seu-bucket`). Configure as políticas de acesso para que suas funções Lambda possam ler e escrever no bucket.
- **Upload dos Documentos:**  
  Faça o upload do arquivo `juridicos.zip` para o bucket.

### 2. Configurar as Funções Lambda
- **Criação e Deploy:**  
  Crie a função Lambda na região desejada (por exemplo, `us-east-1`) utilizando os arquivos do projeto:
  - Função Lambda para indexação: Responsável por extrair textos, gerar embeddings e exportar o índice para o S3.
- **Permissões:**  
  Configure as permissões para que as funções Lambda possam acessar:
  - **S3:** Para leitura dos PDFs e upload/download do índice.
  - **Amazon Bedrock:** Para invocar os modelos.
  - **ChromaDB:** Para criar e acessar recursos temporários (ex.: `/tmp`).
- **Variáveis de Ambiente:**  
  Configure as seguintes variáveis para cada função:
  - `S3_BUCKET_NAME`
  - `S3_DOCUMENTS_KEY`
  - `S3_EMBEDDINGS_KEY`
  - `TELEGRAM_BOT_TOKEN`
 
  Depois que executar a lambda_function e gerar os embeddings, gerar o indice e salvar no s3, vá para -> **Configurações de tempo de execução** e **MUDE** o **MANIPULADOR** para **telegram_bot.lambda_handler**

### 3. Configurar a API Gateway
- **Criação da API:**  
  Crie uma API REST ou HTTP usando o API Gateway que redirecione as requisições para a função Lambda de consulta.
- **Integração com Lambda:**  
  Configure a integração entre o API Gateway e a função Lambda (por exemplo, mapeando o método POST).
- **Webhooks do Telegram:**  
  Configure o webhook do bot do Telegram para usar a URL da API Gateway (exemplo: `https://<id-da-api>.execute-api.<região>.amazonaws.com/<stage>`).

### 4. Criar e Configurar o Bot no Telegram
- **Criação do Bot:**  
  Utilize o [BotFather](https://core.telegram.org/bots#botfather) para criar um novo bot e obter o `TELEGRAM_BOT_TOKEN`.
- **Configuração do Webhook:**  
  Configure o webhook do bot com a URL da API Gateway:
  ```bash
  curl -X POST "https://api.telegram.org/bot<SEU_TOKEN>/setWebhook?url=https://<id-da-api>.execute-api.<região>.amazonaws.com/<stage>"
  ```
   
  ## ❗Dificuldades

- Otimização das layers para ser utilizada na Lambda
- Utilização do Amazon Bedrock para retornar respostas com base nos arquivos
- Implementação do bot ao telegram"
