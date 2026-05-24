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

            if target.type == FSObjectType.FILE:
                ref_id = target.ref_id
                return Stream(
                    file_streamer(self.root_dir / ref_id),
                    media_type=get_mime_type(target.name),
                )
            elif target.type == FSObjectType.DIR:
                listdir = list(map(FSObjectDto.from_entity, target.children))
                parent_dto = FSObjectDto.from_entity(target.parent)
                parent_dto.name = '..'
                listdir.append(parent_dto)
                return listdir

            raise HTTPException(status_code=500)

    def create_dir(self, full_path: str) -> DirDto:
        with self.get_session() as session:
            if session.exists_by_path(full_path):
                raise HTTPException(status_code=400)

            last_slash = full_path.rfind('/')
            if last_slash == 0:
                parent_path = '/'
            else:
                parent_path = full_path[:last_slash]
            name = full_path[last_slash:]

            parent = session.get_by_path(parent_path)
            if not parent:
                raise HTTPException(status_code=400)
            new_dir = session.create(FSObject(
                name=name,
                full_path=full_path,
                ref_id=str(uuid.uuid4()).replace('-', ''),
                type=FSObjectType.DIR,
                parent=parent,
            ))
            return DirDto.from_entity(new_dir)

    async def create_file(self, target_dir, data) -> FileDto:
        with self.get_session() as session:
            parent = session.get_by_path(target_dir)
            if not parent:
                raise HTTPException(status_code=400)

            full_path = (Path(parent.full_path) / data.filename)
            dup_idx = 0
            while session.exists_by_path(full_path.as_posix()):
                dup_idx += 1
                full_path = full_path.with_stem(Path(data.filename).stem + f' ({dup_idx})')

            print(full_path.as_posix())

            ref_id = str(uuid.uuid4()).replace('-', '')
            write_path = self.root_dir / ref_id

            with open(write_path, 'wb') as f:
                chunk_size = 1024 * 1024
                chunk = await data.read(chunk_size)
                while chunk:
                    f.write(chunk)
                    chunk = await data.read(chunk_size)

            target_dir = target_dir if target_dir else '/'
            parent = session.get_by_path(target_dir)
            if not parent:
                raise HTTPException(status_code=400)
            new_file = session.create(FSObject(
                name=data.filename,
                full_path=full_path.as_posix(),
                ref_id=ref_id,
                type=FSObjectType.FILE,
                parent=parent,
            ))
            return FileDto.from_entity(new_file)

    async def rename(self, full_path: str, new_name: str):
        with self.get_session() as session:
            target = session.get_by_path(full_path)
            if not target:
                raise HTTPException(status_code=404)

            siblings = set(child.name for child in target.parent.children)
            if new_name in siblings:
                raise HTTPException(status_code=400)

            old_name_start = full_path.rfind('/') + 1
            new_path = full_path[:old_name_start] + new_name
            old_name_end = len(full_path)
            target.name = new_name
            target.full_path = new_path
            if target.type == FSObjectType.FILE:
                return FileDto.from_entity(target)

            new_basepath = new_path
            for child in session.read_all_descendants(full_path):
                origin_path = child.full_path
                renamed_path = new_basepath + origin_path[old_name_end:]
                child.full_path = renamed_path

            return DirDto.from_entity(target)

    async def delete(self, full_path: str, rmtree: bool):
        with self.get_session() as session:
            target = session.get_by_path(full_path)
            if not target:
                raise HTTPException(status_code=404)

            if target.type == FSObjectType.FILE:
                (self.root_dir / target.ref_id).unlink(missing_ok=True)
                session.delete(target)
                return

            elif target.type == FSObjectType.DIR:
                if not rmtree:
                    raise HTTPException(status_code=403)
                for file in session.read_all_descendant_files(full_path):
                    (self.root_dir / file.ref_id).unlink(missing_ok=True)
                session.delete(target)
                return

            raise HTTPException(status_code=500)
