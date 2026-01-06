import os.path
import uuid
from typing import Iterable

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from models import FSObject, FSObjectType, FSObjectDto


class Repository:
    def __init__(self, connection_string: str = 'sqlite:///test.sqlite'):
        self.engine = create_engine(connection_string)
        self.session_maker = sessionmaker(
            autoflush=True,
            bind=self.engine,
        )
        self.session = None

    def __call__(self, *args, **kwargs):
        self.session = self.session_maker()
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.commit()
        self.session.close()
        self.session = None


class FSRepository(Repository):
    def create(self, dto: FSObjectDto, parent_path: str) -> FSObjectDto:
        name = dto.name
        parent = self.get_by_path(parent_path)
        file_type = dto.type
        new_file = FSObject(
            name=name,
            full_path=os.path.join(parent.full_path, name),
            ref_id=str(uuid.uuid4()).replace('-', ''),
            type=FSObjectType.FILE if file_type == 'file' else FSObjectType.DIR,
            parent_id=parent.id,
        )
        self.session.add(new_file)
        return FSObjectDto.from_entity(new_file)

    def get_by_path(self, full_path: str) -> FSObjectDto:
        entity = self.session.scalar(select(FSObject).where(FSObject.full_path == full_path))
        if not entity:
            raise ValueError('not found')
        return FSObjectDto.from_entity(entity)

    def get_by_id(self, pk: int) -> FSObjectDto:
        entity = self.session.get(FSObject, pk)
        if not entity:
            raise ValueError('not found')
        return FSObjectDto.from_entity(entity)

    def listdir(self, dir_id: int) -> Iterable[FSObjectDto]:
        return map(FSObjectDto.from_entity, self.session.scalars(select(FSObject).where(FSObject.parent_id == dir_id)))
