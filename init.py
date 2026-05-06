from pathlib import Path

import config
from beans import root_dir
from models import FSObject, Base, FSObjectType
from repo import RepositoryFactory, FSRepository

ROOT_DIR = config.ROOT_DIR
DB_URL = config.DB_URL

repo_factory = RepositoryFactory()


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
        try:
            session.get_by_path('/')
        except ValueError:
            print('root directory does\'nt exist, creating')
            session.create_root()


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
                    session.delete(child)
                    continue
                else:
                    file = fs_summary.pop(child.name)
                if child.type != file['type']:
                    print(f'{child.name} was not {child.type}')
                    child.type = file['type']
                    fs_db_diff.append(child)

                if file['type'] == FSObjectType.DIR:
                    inner_dirs.append((file['path_obj'], child))

            session.update_all(fs_db_diff)
            for inner_dir in inner_dirs:
                check_dir(*inner_dir)

        check_dir(root_dir, root_entity)


def init():
    check_schema()
    if not root_dir.exists():
        root_dir.mkdir(parents=True)
    elif root_dir.is_file():
        raise FileExistsError(f'{root_dir} exists and is not a directory')

    compare_fs_db(root_dir)


if __name__ == "__main__":
    compare_fs_db()
