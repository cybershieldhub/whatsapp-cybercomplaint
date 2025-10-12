import os
from dotenv import load_dotenv

load_dotenv()  # this loads .env automatically

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./test.db')
TW_SID = os.getenv('TW_SID')
TW_TOKEN = os.getenv('TW_TOKEN')
TW_WHATSAPP_FROM = os.getenv('TW_WHATSAPP_FROM')
S3_BUCKET = os.getenv('S3_BUCKET')
SELENIUM_WORKER_URL = os.getenv('SELENIUM_WORKER_URL')
SECRET_KEY = os.getenv('SECRET_KEY')
