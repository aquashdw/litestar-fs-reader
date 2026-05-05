from pathlib import Path

from models import FSObject, Base, FSObjectType
from repo import RepositoryFactory, FSRepository

repo_factory = RepositoryFactory()


def check_schema(connection_string: str = 'sqlite:///test.sqlite'):
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
            print('root directory doest exist, creating')
            session.create_root()


def compare_fs_db(root_dir: str = '.root', connection_string: str = 'sqlite:///test.sqlite'):
    """
    starting with root_dir, compare database records with the actual filesystem.
    """
    root_path = Path(root_dir).absolute()
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

        check_dir(root_path, root_entity)


if __name__ == "__main__":
    start_path = "./.root"
    # check_schema()
    # print(f"Starting recursive list from: {os.path.abspath(start_path)}\n")
    # list_recursive(start_path)
    # root = Path(start_path)
    # print([file.name for file in root.iterdir()])
    compare_fs_db()
