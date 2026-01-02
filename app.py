import os
from dataclasses import dataclass
from pathlib import Path

from typing import List, Union, Literal
from litestar import Litestar, get, Request
from dotenv import load_dotenv
from litestar.exceptions import HTTPException

load_dotenv()
ROOT_DIR = os.environ.get('ROOT_DIR', '.')
ROOT_DIR = os.path.abspath(ROOT_DIR)
if ROOT_DIR.endswith('/'):
    ROOT_DIR = ROOT_DIR[:-1]


@dataclass
class Item:
    name: str
    path: str
    type: Union[Literal['file'] | Literal['dir'], str]

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
    path = Path(ROOT_DIR + full_path)
    # no file nor dir
    if not path.exists():
        raise HTTPException(status_code=404)
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
