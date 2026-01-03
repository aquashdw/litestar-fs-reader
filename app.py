import os
from csv import excel
from dataclasses import dataclass
from pathlib import Path

from typing import List, Union, Literal
from litestar import Litestar, get, Request
from dotenv import load_dotenv
from litestar.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError, NoResultFound

from models import FileDto, DirDto, FSObjectDto
from repo import FSRepository

load_dotenv()
ROOT_DIR = os.environ.get('ROOT_DIR', '.')
ROOT_DIR = os.path.abspath(ROOT_DIR)
if ROOT_DIR.endswith('/'):
    ROOT_DIR = ROOT_DIR[:-1]

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
    return [
        Item(
            item.name,
            '/' + item.name,
            'file' if item.is_file() else 'dir'
        ) for item in Path(ROOT_DIR).iterdir()
    ]


@get('/{full_path:path}')
async def get_path(
        request: Request,
        full_path: str) -> List[Item] | bytes:
    with repository() as session:
        try:
            target = session.get_by_path(full_path)
        except ValueError:
            raise HTTPException(status_code=404)
        path = Path(ROOT_DIR + target.full_path)
        # no file nor dir
        if not path.exists():
            # TODO log: file is removed without user notice?
            raise HTTPException(status_code=500)

        match target.type:
            case 'dir':
                # TODO add parent
                return list(session.listdir(target.id))
            case 'file':
                # TODO
                raise HTTPException(status_code=501)

    raise HTTPException(status_code=500)
    # if dir, list dir + parent dir
    if path.is_dir():
        iter_dir = [
            Item(
                item.name,
                str(item).replace(ROOT_DIR, ''),
                'file' if item.is_file() else 'dir'
            ) for item in path.iterdir()
        ]
        last_slash = full_path.rfind('/')
        if last_slash == 0:
            iter_dir.append(Item(
                '..',
                '/',
                'dir'
            ))
        else:
            iter_dir.append(Item(
                '..',
                full_path[:last_slash],
                'dir',
            ))
        return iter_dir
    # else return as bytes
    else:
        return path.read_bytes()


app = Litestar([index, get_path])
