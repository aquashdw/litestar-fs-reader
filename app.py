import os
from pathlib import Path

from typing import List, Union, Literal
from litestar import Litestar, get, Request
from dotenv import load_dotenv

load_dotenv()
ROOT_DIR = os.environ.get('ROOT_DIR', '.')

@get('/')
async def index() -> List[str]:
    return [str(item) for item in Path(ROOT_DIR).iterdir()]


@get('/{full_path:path}')
async def get_path(
        request: Request,
        full_path: str,
        target: Union[Literal['dir'] | Literal['file']] = 'file') -> List[str]:
    return [str(item) for item in Path(ROOT_DIR).iterdir()]


app = Litestar([index, get_path])
