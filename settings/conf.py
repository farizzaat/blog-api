from pathlib import Path

from decouple import Config, RepositoryEnv

ENV_FILE = Path(__file__).resolve().parent / ".env"
config = Config(RepositoryEnv(ENV_FILE))


BLOG_ENV_ID = config("BLOG_ENV_ID", default="local")
BLOG_SECRET_KEY = config("BLOG_SECRET_KEY")
BLOG_DEBUG = config("BLOG_DEBUG", default=False, cast=bool)

BLOG_DB_NAME = config("BLOG_DB_NAME", default="blog_api")
BLOG_DB_USER = config("BLOG_DB_USER", default="postgres")
BLOG_DB_PASSWORD = config("BLOG_DB_PASSWORD", default="")
BLOG_DB_HOST = config("BLOG_DB_HOST", default="localhost")
BLOG_DB_PORT = config("BLOG_DB_PORT", default="5432")