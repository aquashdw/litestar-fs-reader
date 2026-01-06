import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal

from dotenv import load_dotenv
from litestar import Litestar, get, post
from litestar.exceptions import HTTPException

from models import FSObjectDto, DirDto
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


@get('/{full_path:path}')
async def get_obj(full_path: str) -> List[Item] | bytes:
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
                return path.read_bytes()

    raise HTTPException(status_code=500)


@post('/{full_path:path}')
async def create_obj(full_path: str, mkdir: str | None) -> Item:
    path = Path(ROOT_DIR + full_path)
    if full_path.endswith('/'):
        full_path = full_path[:-1]
    if path.exists():
        print('file or dir exists')
        raise HTTPException(status_code=400)
    with repository() as session:
        if mkdir is not None:
            last_slash = full_path.rfind('/')
            path.mkdir()
            parent_path = full_path[:last_slash]
            if not parent_path:
                parent_path = '/'
            dto = DirDto(
                id=None,
                name=path.name,
                full_path=full_path,
                ref_id=None,
                parent_id=None,
            )
            dto = session.create(dto, parent_path)
            return Item.from_dto(dto)
        else:
            # TODO add file
            raise HTTPException(status_code=501)


app = Litestar([index, get_obj, create_obj])
