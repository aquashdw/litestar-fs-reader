import os

from dotenv import load_dotenv

load_dotenv()
ROOT_DIR = os.environ.get('ROOT_DIR', '.')
DB_URL = os.environ.get('DB_URL', 'sqlite:///test.sqlite')
KEY_DIR = os.environ.get('KEY_DIR', '.key')
