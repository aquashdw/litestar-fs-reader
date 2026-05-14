import os
import uuid
from pathlib import Path
from typing import Iterable

from litestar.exceptions import HTTPException
from litestar.response import Stream

from utils import file_streamer, get_mime_type
from .models import FSObjectDto, FSObject, FSObjectType, DirDto, FileDto
from .repo import FSRepository, RepositoryFactory


class FSService:
    def __init__(self, repo_factory: RepositoryFactory, root_dir: Path):
        self.repo_factory = repo_factory
        self.root_dir = root_dir

    def get_session(self):
        return self.repo_factory(FSRepository)

    def list_dir(self, full_path: str) -> Iterable[FSObjectDto]:
        with self.get_session() as session:
            dir_entity = session.get_by_path(full_path)
            return list(map(FSObjectDto.from_entity, dir_entity.children))

    def list_root(self) -> Iterable[FSObjectDto]:
        return self.list_dir('/')

    async def get_obj(self, full_path: str) -> Iterable[FSObjectDto] | Stream:
        with self.get_session() as session:
            target = session.get_by_path(full_path)
            if not target:
                raise HTTPException(status_code=404)
            ph_path = self.root_dir / target.full_path[1:]
            if not ph_path.exists():
                raise HTTPException(status_code=500)

            if target.type == FSObjectType.DIR and ph_path.is_dir():
                listdir = list(map(FSObjectDto.from_entity, target.children))
                parent_dto = FSObjectDto.from_entity(target.parent)
                parent_dto.name = '..'
                listdir.append(parent_dto)
                return listdir
            elif target.type == FSObjectType.FILE and ph_path.is_file():
                return Stream(
                    file_streamer(ph_path),
                    media_type=get_mime_type(target.name),
                )
            # file dir missmatch
            raise HTTPException(status_code=500)

    def create_dir(self, full_path: str) -> DirDto:
        path = self.root_dir / full_path[1:]
        if path.exists():
            print('file or dir exists')
            raise HTTPException(status_code=400)
        path.mkdir()
        last_slash = full_path.rfind('/')
        if last_slash == 0:
            parent_path = '/'
        else:
            parent_path = full_path[:last_slash]

        with self.get_session() as session:
            parent = session.get_by_path(parent_path)
            if not parent:
                raise HTTPException(status_code=400)
            new_dir = session.create(FSObject(
                name=path.name,
                full_path=(Path(parent.full_path) / path.name).as_posix(),
                ref_id=str(uuid.uuid4()).replace('-', ''),
                type=FSObjectType.DIR,
                parent_id=parent.id,
            ))
            return DirDto.from_entity(new_dir)

    async def create_file(self, target_dir, data) -> FileDto:
        path = self.root_dir / target_dir[1:]

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
            target_dir = target_dir if target_dir else '/'
            parent = session.get_by_path(target_dir)
            if not parent:
                raise HTTPException(status_code=400)
            new_file = session.create(FSObject(
                name=name,
                full_path=(Path(parent.full_path) / name).as_posix(),
                ref_id=str(uuid.uuid4()).replace('-', ''),
                type=FSObjectType.FILE,
                parent_id=parent.id,
            ))
            return FileDto.from_entity(new_file)
