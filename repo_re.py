from abc import ABC
from typing import List

from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import sessionmaker

from models import FSObject, FSObjectType


class RepositorySession(ABC):
    """
    Abstract Repository Session to be implemented by children
    who actually decides how to interact with database.
    """

    def __init__(self, session, *args, **kwargs):
        self.session = session

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()
        self.session = None


class RepositoryFactory:
    """
    Factory class to create repository sessions.
    """

    def __init__(self, connection_string: str = 'sqlite:///test.sqlite'):
        self.engine = create_engine(connection_string)
        self.session_maker = sessionmaker(
            autoflush=True,
            bind=self.engine,
        )

        self._inspector = inspect(self.engine)

    @property
    def inspector(self):
        return self._inspector

    def __call__(self, target: type[RepositorySession], *args, **kwargs) -> RepositorySession:
        return target(self.session_maker(), *args, **kwargs)


class FSRepository(RepositorySession):
    def create_root(self) -> FSObject:
        root = FSObject(
            name='/',
            full_path='/',
            ref_id='root',
            type=FSObjectType.DIR
        )
        self.session.add(root)
        return root

    def create(self, fs_object: FSObject):
        self.session.add(fs_object)
        self.session.flush()
        return fs_object

    def get_by_id(self, pk: int) -> FSObject:
        entity = self.session.get(FSObject, pk)
        if not entity:
            raise ValueError('not found')
        return entity

    def get_by_path(self, full_path: str) -> FSObject:
        entity = self.session.scalar(select(FSObject).where(FSObject.full_path == full_path))
        if not entity:
            raise ValueError('not found')
        return entity

    def listdir(self, dir_obj: FSObject) -> List[FSObject]:
        return self.session.scalars(select(FSObject).where(FSObject.parent_id == dir_obj.id))
