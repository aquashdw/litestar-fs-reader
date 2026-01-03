import enum
import uuid
from dataclasses import dataclass
from typing import List, Type, Literal

from sqlalchemy import Integer, Text, Enum, ForeignKey, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session


class Base(DeclarativeBase):
    pass


class FSObjectType(enum.Enum):
    DIR = 'dir'
    FILE = 'file'


class FSObject(Base):
    __tablename__ = 'fs_object'
    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    name: Mapped[str] = mapped_column(Text())
    full_path: Mapped[str] = mapped_column(Text(), unique=True)
    ref_id: Mapped[str] = mapped_column(Text(), unique=True)
    type: Mapped[FSObjectType] = mapped_column(Enum(FSObjectType), default=FSObjectType.DIR)
    parent_id: Mapped[int | None] = mapped_column(Integer(), ForeignKey('fs_object.id'))
    parent: Mapped[Type['FSObject'] | None] = relationship(
        'FSObject',
        remote_side=[id],
        back_populates='children'
    )
    children: Mapped[List['FSObject'] | None] = relationship(
        'FSObject',
        back_populates='parent',
    )


@dataclass
class FSObjectDto:
    id: int | None
    name: str
    full_path: str
    ref_id: str | None
    parent_id: int | None
    type: str | None

    @classmethod
    def from_entity(cls, entity: FSObject):
        match entity.type:
            case FSObjectType.DIR:
                return DirDto(
                    id=entity.id,
                    name=entity.name,
                    full_path=entity.full_path,
                    ref_id=entity.ref_id,
                    parent_id=entity.parent_id,
                )
            case FSObjectType.FILE:
                return FileDto(
                    id=entity.id,
                    name=entity.name,
                    full_path=entity.full_path,
                    ref_id=entity.ref_id,
                    parent_id=entity.parent_id,
                )


@dataclass
class FileDto(FSObjectDto):
    type: Literal['file'] = 'file'


@dataclass
class DirDto(FSObjectDto):
    type: Literal['dir'] = 'dir'


if __name__ == '__main__':
    engine = create_engine('sqlite:///test.sqlite')

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        root = FSObject(
            name='/',
            full_path='/',
            ref_id='root',
            type=FSObjectType.DIR,
        )
        foo = FSObject(
            name='foo',
            full_path='/foo',
            ref_id=str(uuid.uuid4()).replace('-', ''),
            type=FSObjectType.DIR,
            parent=root,
        )
        bar = FSObject(
            name='bar',
            full_path='/foo/bar',
            ref_id=str(uuid.uuid4()).replace('-', ''),
            type=FSObjectType.DIR,
            parent=foo,
        )
        baz = FSObject(
            name='baz',
            full_path='/foo/bar/baz',
            ref_id=str(uuid.uuid4()).replace('-', ''),
            type=FSObjectType.FILE,
            parent=foo,
        )

        test_audio = FSObject(
            name='test_audio.mp3',
            full_path='/test_audio.mp3',
            ref_id=str(uuid.uuid4()).replace('-', ''),
            type=FSObjectType.FILE,
            parent=root,
        )
        test_video = FSObject(
            name='test_video.mp4',
            full_path='/test_video.mp4',
            ref_id=str(uuid.uuid4()).replace('-', ''),
            type=FSObjectType.FILE,
            parent=root,
        )

        session.add_all([
            root,
            foo,
            bar,
            baz,
            test_audio,
            test_video,
        ])
        session.commit()
