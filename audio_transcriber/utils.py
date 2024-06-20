import os
import dotenv


def get_env(key: str, default: str | None = None) -> str | None:
    if key in os.environ:
        return os.environ[key]

    dotenv_values = dotenv.dotenv_values()
    if dotenv_values and key in dotenv_values:
        return dotenv_values[key]

    return default


def file_exists(file_path: str) -> bool:
    return os.path.exists(file_path) and os.path.isfile(file_path)


def is_url(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")
