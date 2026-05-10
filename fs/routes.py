from typing import List, Annotated, Optional, Iterable

from litestar import get, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.response import Stream

from singletons import service
from .models import FSObjectDto


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


handlers = [index, get_obj, create_obj]
