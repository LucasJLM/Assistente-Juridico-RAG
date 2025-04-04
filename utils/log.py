import logging

# Configuração básica de logging para CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_logger():
    return logger