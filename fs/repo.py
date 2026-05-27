from abc import ABC
from typing import List, Optional, Iterable

from sqlalchemy import create_engine, inspect, select, exists
from sqlalchemy.orm import sessionmaker

from .models import FSObject, FSObjectType


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

    def create(self, fs_object: FSObject) -> FSObject:
        self.session.add(fs_object)
        self.session.flush()
        return fs_object

    def delete(self, fs_object: FSObject) -> None:
        self.session.delete(fs_object)

    def update_all(self, fs_objects: Iterable[FSObject]) -> None:
        self.session.add_all(fs_objects)

    def get_by_id(self, pk: int) -> Optional[FSObject]:
        entity = self.session.get(FSObject, pk)
        return entity

    def get_by_path(self, full_path: str) -> Optional[FSObject]:
        entity = self.session.scalar(select(FSObject).where(FSObject.full_path == full_path))
        return entity

    def get_by_ref(self, ref_id: str) -> Optional[FSObject]:
        return self.session.scalar(select(FSObject).where(FSObject.ref_id == ref_id))

    def exists_by_path(self, full_path: str) -> bool:
        return self.session.scalar(exists().where(FSObject.full_path == full_path).select())

    def read_all_descendants(self, full_path: str = '') -> Iterable[FSObject]:
        return self.session.scalars(select(FSObject).where(FSObject.full_path.like(f'{full_path}/%')))

    def read_all_descendant_files(self, full_path: str = '') -> Iterable[FSObject]:
        return self.session.scalars(
            select(FSObject).where(
                FSObject.full_path.like(f'{full_path}/%'),
                FSObject.type == FSObjectType.FILE)
        )

    def listdir(self, dir_obj: FSObject) -> List[FSObject]:
        return self.session.scalars(select(FSObject).where(FSObject.parent_id == dir_obj.id))
