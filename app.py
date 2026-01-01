import os
from pathlib import Path

from typing import List
from litestar import Litestar, get
from dotenv import load_dotenv

load_dotenv()
ROOT_DIR = os.environ.get('ROOT_DIR', '.')

@get('/')
def index() -> List[str]:
    return [str(item) for item in Path(ROOT_DIR).iterdir()]


app = Litestar([index])
