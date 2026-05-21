from pathlib import Path

from fs.models import FSObject, Base
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
    fs_pool = set(obj.name for obj in root_dir.iterdir())
    with repo_factory(FSRepository) as session:
        missing = set(entity for entity in session.read_all_descendant_files() if entity.ref_id not in fs_pool)
        # TODO create a report
        print(missing)


def init():
    check_fs()
    check_schema()
    compare_fs_db(root_dir)
    create_key()


if __name__ == "__main__":
    check_schema()
    compare_fs_db(root_dir)
