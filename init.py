import uuid
from pathlib import Path

from fs.models import FSObject, Base, FSObjectType
from fs.repo import FSRepository
from singletons import root_dir, repo_factory
from utils import create_key


def check_schema():
    """
    Check the database of connection string to see if required tables exists
    Create if it doesn't exist
    """

    # connected with Repository
    inspector = repo_factory.inspector
    if not inspector.has_table(FSObject.__tablename__):
        print('table does not exist, creating')
        Base.metadata.create_all(repo_factory.engine)

    with repo_factory(FSRepository) as session:
        if not session.get_by_path('/'):
            print('root directory doesn\'t exist, creating')
            session.create_root()


def check_fs():
    """
    Configure filesystem or fail
    """
    if not root_dir.exists():
        root_dir.mkdir(parents=True)
    elif root_dir.is_file():
        raise FileExistsError(f'{root_dir} exists and is not a directory')


def compare_fs_db(root_dir: Path):
    """
    starting with root_dir, compare database records with the actual filesystem.
    """
    with repo_factory(FSRepository) as session:
        root_entity = session.get_by_path('/')

        def check_dir(path: Path, cwd: FSObject):
            if path.is_file():
                return
            fs_summary = {}
            for obj in path.iterdir():
                fs_summary[obj.name] = {
                    'path_obj': obj,
                    'type': FSObjectType.FILE if obj.is_file() else FSObjectType.DIR,
                }

            fs_db_diff = []
            inner_dirs = []
            for child in session.listdir(cwd):
                if child.name not in fs_summary:
                    print(f'{child.name} not found in fs')
                    # session.delete(child)
                    continue
                else:
                    file = fs_summary.pop(child.name)
                if child.type != file['type']:
                    print(f'{child.name} was not {child.type}')
                    child.type = file['type']
                    fs_db_diff.append(child)

                if file['type'] == FSObjectType.DIR:
                    inner_dirs.append((file['path_obj'], child))

            for key in fs_summary:
                name = key
                full_path = (Path(cwd.full_path) / name).as_posix()
                ref_id = str(uuid.uuid4()).replace('-', '')
                file_type = fs_summary[name]['type']
                new_file = session.create(FSObject(
                    name=name,
                    full_path=full_path,
                    ref_id=ref_id,
                    type=file_type,
                    parent=cwd,
                ))
                if new_file.type == FSObjectType.DIR:
                    inner_dirs.append((fs_summary[name]['path_obj'], new_file))

            session.update_all(fs_db_diff)
            for inner_dir in inner_dirs:
                check_dir(*inner_dir)

        check_dir(root_dir, root_entity)


def init():
    check_fs()
    check_schema()
    compare_fs_db(root_dir)
    create_key()


if __name__ == "__main__":
    check_schema()
    compare_fs_db(root_dir)
