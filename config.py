import os

from dotenv import load_dotenv

load_dotenv()
ROOT_DIR = os.environ.get('ROOT_DIR', '.')
DB_URL = os.environ.get('DB_URL', 'sqlite:///test.sqlite')
KEY_DIR = os.environ.get('KEY_DIR', '.key')

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
REDIS_USER = os.environ.get('REDIS_USER', 'default')
REDIS_PASS = os.environ.get('REDIS_PASS', 'systempass')
