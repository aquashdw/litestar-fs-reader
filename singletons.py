from pathlib import Path

import redis

import config
from fs.repo import RepositoryFactory
from fs.service import FSService

repo_factory = RepositoryFactory(config.DB_URL)
root_dir = Path(config.ROOT_DIR).absolute()
service = FSService(repo_factory, root_dir)
redis_connection = redis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    username=config.REDIS_USER,
    password=config.REDIS_PASS,
    decode_responses=True,
)
