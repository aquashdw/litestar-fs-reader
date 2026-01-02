import enum
import uuid
from typing import List, Type

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
            parent=bar,
        )
        session.add_all([root, foo, bar, baz])
        session.commit()
