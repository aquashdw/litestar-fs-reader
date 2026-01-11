import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Annotated

from dotenv import load_dotenv
from litestar import Litestar, get, post, Response
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.params import Body

from models import FSObjectDto, DirDto, FileDto
from repo import FSRepository

load_dotenv()
ROOT_DIR = os.environ.get('ROOT_DIR', '.')
ROOT_DIR = os.path.abspath(ROOT_DIR)
if ROOT_DIR.endswith('/'):
    ROOT_DIR = ROOT_DIR[:-1]
if not os.path.exists(ROOT_DIR):
    os.mkdir(ROOT_DIR)
elif os.path.isfile(ROOT_DIR):
    raise FileExistsError(f'{ROOT_DIR} exists and is not a directory')

repository = FSRepository()


@dataclass
class Item:
    name: str
    path: str
    type: Literal['file'] | Literal['dir'] | str

    @classmethod
    def from_dto(cls, dto: FSObjectDto):
        return cls(
            name=dto.name,
            path=dto.full_path,
            type=dto.type
        )


@get('/')
async def index() -> List[Item]:
    with repository() as session:
        try:
            root = session.get_by_path('/')
            return list(session.listdir(root.id))
        except ValueError:
            # TODO log: root doesn't exist in db?
            print('root obj not in db')
            raise HTTPException(status_code=500)


def get_mime_type(filename: str) -> str:
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'application/octet-stream'


@get('/{full_path:path}')
async def get_obj(full_path: str) -> List[Item] | Response:
    with repository() as session:
        try:
            target = session.get_by_path(full_path)
        except ValueError:
            raise HTTPException(status_code=404)
        path = Path(ROOT_DIR + target.full_path)
        # no file nor dir
        if not path.exists():
            # TODO log: file is removed without user notice?
            print('file removed without db update')
            raise HTTPException(status_code=500)
        match target.type:
            case 'dir':
                iter_dir = list(session.listdir(target.id))
                parent = session.get_by_id(target.parent_id)
                iter_dir.append(Item('..', parent.full_path, 'dir',))
                return iter_dir
            case 'file':
                return Response(
                    content=path.read_bytes(),
                    media_type=get_mime_type(path.name),
                )

    raise HTTPException(status_code=500)


@post('/{full_path:path}')
async def create_obj(
        full_path: str,
        isdir: str | None = None,
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)] = None,
) -> Item:
    if full_path.endswith('/'):
        full_path = full_path[:-1]
    path = Path(ROOT_DIR + full_path)
    if isdir is not None:

        if path.exists():
            print('file or dir exists')
            raise HTTPException(status_code=400)
        path.mkdir()

        last_slash = full_path.rfind('/')
        parent_path = full_path[:last_slash]
        if not parent_path:
            parent_path = '/'

        with repository() as session:
            dto = DirDto(
                id=None,
                name=path.name,
                full_path=None,
                ref_id=None,
                parent_id=None,
            )
            dto = session.create(dto, parent_path)
            return Item.from_dto(dto)

    if not path.exists() or not path.is_dir():
        print('target dir not found or is not a directory')
        raise HTTPException(status_code=400)
    file_path = path / data.filename
    dup_idx = 0
    while file_path.exists():
        dup_idx += 1
        file_path = file_path.with_stem(os.path.splitext(data.filename)[0] + f' ({dup_idx})')

    content = await data.read()
    with open(file_path, 'wb') as f:
        f.write(content)
    with repository() as session:
        dto = FileDto(
            id=None,
            name=file_path.name,
            full_path=None,
            ref_id=None,
            parent_id=None,
        )
        dto = session.create(dto, full_path)
        return Item.from_dto(dto)


app = Litestar([index, get_obj, create_obj])
