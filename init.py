from pathlib import Path

from models import FSObject, Base, FSObjectType
from repo import RepositoryFactory, FSRepository
from repo_bak import FSRepository as repo_before

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


def compare_fs_db(root_dir: str = '.', connection_string: str = 'sqlite:///test.sqlite'):
    """
    starting with root_dir, compare database records with the actual filesystem.
    """
    root_path = Path(root_dir).absolute()
    repo = repo_before(connection_string)
    with repo() as session:
        root_entity = session.get_by_path('/')

        def check_dir(path: Path, parent_dto: FSObject):
            if path.is_file():
                return

            fs_summary = {}
            for obj in path.iterdir():
                fs_summary[obj.name] = {
                    'path_obj': obj,
                    'type': FSObjectType.FILE if obj.is_file() else FSObjectType.DIR,
                }
            print(len(fs_summary))

            fd_db_diff = []
            inner_dirs = []
            for child in repo.listdir(parent_dto.id):

                # TODO remove file not in filesystem
                if child.name not in fs_summary:
                    continue
                else:
                    file = fs_summary.pop(child.name)
                if child.type != file['type']:
                    child.type = file['type']
                    fd_db_diff.append(child)
                    # TODO alter if file dir mismatch
                    pass

                if file['type'] == FSObjectType.DIR:
                    inner_dirs.append((file['path_obj'], child))

            print(len(fs_summary))
            for inner_dir in inner_dirs:
                check_dir(*inner_dir)

        check_dir(root_path, root_entity)


if __name__ == "__main__":
    start_path = "."
    # check_schema()
    # print(f"Starting recursive list from: {os.path.abspath(start_path)}\n")
    # list_recursive(start_path)
    # root = Path(start_path)
    # print([file.name for file in root.iterdir()])
    compare_fs_db()
