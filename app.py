import os
from pathlib import Path
from typing import List, Annotated, Optional, Iterable

from dotenv import load_dotenv
from litestar import Litestar, get, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.response import Stream

from models import FSObjectDto
from repo import FSRepository
from repo_re import RepositoryFactory
from service import FSService

load_dotenv()
ROOT_DIR = Path(os.environ.get('ROOT_DIR', '.')).absolute()
if not ROOT_DIR.exists():
    ROOT_DIR.mkdir(parents=True)
elif ROOT_DIR.is_file():
    raise FileExistsError(f'{ROOT_DIR} exists and is not a directory')

repository = FSRepository()
service = FSService(RepositoryFactory(), ROOT_DIR)


@get('/')
async def index() -> Iterable[FSObjectDto]:
    return service.list_root()


@get('/{full_path:path}')
async def get_obj(full_path: str) -> List[FSObjectDto] | Stream:
    return await service.get_obj(full_path)


@post('/{full_path:path}')
async def create_obj(
        full_path: str,
        isdir: str | None = None,
        data: Optional[Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)]] = None,
) -> FSObjectDto:
    if full_path.startswith('/'):
        full_path = full_path[1:]
    return await service.create(full_path, isdir, data)


app = Litestar([index, get_obj, create_obj])
