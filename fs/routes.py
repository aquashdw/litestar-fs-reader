from typing import List, Iterable, Optional, Annotated

from litestar import get, post, Request, delete, patch
from litestar.params import QueryParameter
from litestar.response import Stream

from singletons import service
from .models import FSObjectDto


@get('/')
async def index() -> Iterable[FSObjectDto]:
    return service.list_root()


@get('/{full_path:path}')
async def get_obj(full_path: str) -> List[FSObjectDto] | Stream:
    return await service.get_obj(full_path)


@get('/ref', status_code=204)
async def get_obj_by_ref(ref_id: Annotated[str, QueryParameter(name='query')]) -> List[FSObjectDto] | Stream:
    return await service.get_obj_by_ref(ref_id)


@post(['/', '/{full_path:path}'], status_code=201)
async def create_obj(
        request: Request,
        full_path: str = '/',
) -> FSObjectDto:
    if 'isdir' in request.query_params:
        return service.create_dir(full_path)

    data = (await request.form()).get('data')
    return service.create_file(full_path, data)


@patch('/{full_path:path}')
async def rename(
        full_path: str,
        data: FSObjectDto,
) -> FSObjectDto:
    if full_path.endswith('/'):
        full_path = full_path[:-1]
    return service.rename(full_path, data.name)


@delete('/{full_path:path}', status_code=204)
async def delete_target(
        full_path: str,
        rmtree: Optional[str] = None,
) -> None:
    if full_path.endswith('/'):
        full_path = full_path[:-1]
    await service.delete(full_path, rmtree is not None)


handlers = [
    index,
    get_obj,
    get_obj_by_ref,
    create_obj,
    rename,
    delete_target
]
