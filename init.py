from models import FSObject, Base
from repo import FSRepository


def check_schema(connection_string: str = 'sqlite:///test.sqlite'):
    """
    Check the database of connection string to see if required tables exists
    Create if it doesn't exist
    """
    # connected with Repository
    repo = FSRepository(connection_string)
    inspector = repo.create_inspector()
    if not inspector.has_table(FSObject.__tablename__):
        print('table does not exist, creating')
        Base.metadata.create_all(repo.engine)

    with repo() as session:
        try:
            session.get_by_path('/')
        except ValueError:
            print('root directory doest exist, creating')
            session.create_root()


if __name__ == "__main__":
    start_path = "."
    check_schema()
