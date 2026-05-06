from pathlib import Path

import config
from repo import RepositoryFactory
from service import FSService

repo_factory = RepositoryFactory(config.DB_URL)
root_dir = Path(config.ROOT_DIR).absolute()
service = FSService(repo_factory, root_dir)
