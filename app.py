import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Annotated, Optional

from dotenv import load_dotenv
from litestar import Litestar, get, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.params import Body
from litestar.response import Stream

from models import FSObjectDto
from repo import FSRepository
from repo_re import RepositoryFactory
from service import FSService
from utils import file_streamer, get_mime_type

load_dotenv()
ROOT_DIR = Path(os.environ.get('ROOT_DIR', '.')).absolute()
if not ROOT_DIR.exists():
    ROOT_DIR.mkdir(parents=True)
elif ROOT_DIR.is_file():
    raise FileExistsError(f'{ROOT_DIR} exists and is not a directory')

repository = FSRepository()
service = FSService(RepositoryFactory(), ROOT_DIR)


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
    return list(map(Item.from_dto, service.list_root()))


@get('/{full_path:path}')
async def get_obj(full_path: str) -> List[Item] | Stream:
    with repository() as session:
        try:
            target = session.get_by_path(full_path)
        except ValueError:
            raise HTTPException(status_code=404)
        path = ROOT_DIR / target.full_path
        # no file nor dir
        if not path.exists():
            # TODO log: file is removed without user notice?
            print('file removed without db update')
            raise HTTPException(status_code=500)
        match target.type:
            case 'dir':
                iter_dir = list(session.listdir(target.id))
                parent = session.get_by_id(target.parent_id)
                iter_dir.append(Item('..', parent.full_path, 'dir', ))
                return iter_dir
            case 'file':
                return Stream(
                    file_streamer(path),
                    media_type=get_mime_type(path.name),
                )

    raise HTTPException(status_code=500)


@post('/{full_path:path}')
async def create_obj(
        full_path: str,
        isdir: str | None = None,
        data: Optional[Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)]] = None,
) -> Item:
    if full_path.startswith('/'):
        full_path = full_path[1:]
    return Item.from_dto(await service.create(full_path, isdir, data))


app = Litestar([index, get_obj, create_obj])
