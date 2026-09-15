import os

from decouple import Config, RepositoryEnv

ENV_FILE = os.path.join(
    os.path.dirname(__file__),
    "settings",
    ".env",
)

config = Config(RepositoryEnv(ENV_FILE))

BLOG_ENV_ID = config("BLOG_ENV_ID", default="local")

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    f"settings.env.{BLOG_ENV_ID}",
)


def main() -> None:
    """Run administrative tasks."""
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Make sure it is installed."
        ) from exc

    execute_from_command_line(os.sys.argv)


if __name__ == "__main__":
    main()