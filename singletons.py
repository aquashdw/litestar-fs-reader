from pathlib import Path

import config
from fs.repo import RepositoryFactory
from fs.service import FSService

repo_factory = RepositoryFactory(config.DB_URL)
root_dir = Path(config.ROOT_DIR).absolute()
service = FSService(repo_factory, root_dir)
