import os
import uuid
from pathlib import Path
from typing import Annotated, Optional, Iterable

from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.params import Body

from models import FSObjectDto, FSObject, FSObjectType, DirDto, FileDto
from repo_re import FSRepository, RepositoryFactory


class FSService:
    def __init__(self, repo_factory: RepositoryFactory, root_dir: Path):
        self.repo_factory = repo_factory
        self.root_dir = root_dir

    def get_session(self):
        return self.repo_factory(FSRepository)

    def list_root(self) -> Iterable[FSObjectDto]:
        with self.get_session() as session:
            root_entity = session.get_by_path(FSObject.name)
            return list(map(FSObjectDto.from_entity, root_entity.children))

    async def create(
            self,
            full_path: str,
            isdir: str | None = None,
            data: Optional[Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)]] = None,
    ) -> FSObjectDto:
        if full_path.endswith('/'):
            full_path = full_path[:-1]
        if isdir is not None:
            return self.create_dir(full_path)
        return await self.create_file(full_path, data)

    def create_dir(self, full_path: str):
        path = self.root_dir / full_path
        if path.exists():
            print('file or dir exists')
            raise HTTPException(status_code=400)
        path.mkdir()
        last_slash = full_path.rfind('/')
        if last_slash != -1:
            parent_path = full_path[:last_slash]
        else:
            parent_path = '/'

        with self.get_session() as session:
            parent = session.get_by_path(parent_path)
            new_dir = session.create(FSObject(
                name=path.name,
                full_path=os.path.join(parent.full_path, path.name),
                ref_id=str(uuid.uuid4()).replace('-', ''),
                type=FSObjectType.DIR,
                parent_id=parent.id,
            ))
            return DirDto.from_entity(new_dir)

    async def create_file(self, target_dir, data):
        path = self.root_dir / target_dir

        if not path.exists() or not path.is_dir():
            raise HTTPException(status_code=400)
        file_path = path / data.filename
        dup_idx = 0
        while file_path.exists():
            dup_idx += 1
            file_path = file_path.with_stem(os.path.splitext(data.filename)[0] + f' ({dup_idx})')

        with open(file_path, 'wb') as f:
            chunk_size = 1024 * 1024
            chunk = await data.read(chunk_size)
            while chunk:
                f.write(chunk)
                chunk = await data.read(chunk_size)

        with self.get_session() as session:
            name = file_path.name
            parent = session.get_by_path(target_dir)
            new_file = session.create(FSObject(
                name=name,
                full_path=os.path.join(parent.full_path, name),
                ref_id=str(uuid.uuid4()).replace('-', ''),
                type=FSObjectType.FILE,
                parent_id=parent.id,
            ))
            return FileDto.from_entity(new_file)
