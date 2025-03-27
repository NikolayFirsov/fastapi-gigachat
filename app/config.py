import os

from dotenv import load_dotenv

load_dotenv()

# jwt
JWT_SECRET = os.getenv('JWT_SECRET', 'a-very-very-secret-key-for-hs256-sig')

# бд
DB_USER = os.getenv('DB_USER', '')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', '')
DB_HOST = os.getenv('DB_HOST', '')
DB_PORT = os.getenv('DB_PORT', '')

# гигачат
GIGA_TOKEN = os.getenv('GIGA_TOKEN', '')
GIGA_SCOPE = os.getenv('GIGA_SCOPE', '')
GIGA_MODEL = os.getenv('GIGA_MODEL', '')
MAX_TOKENS_FOR_TRIMMER = int(os.getenv('MAX_TOKENS_FOR_TRIMMER', 2500))

# промт
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPT_FILE_PATH = os.path.join(BASE_DIR, 'promt.txt')
DEFAULT_PROMPT = """
Дефолтный промт
"""
