from datetime import UTC, datetime
from pathlib import Path

from dotenv import dotenv_values
from loguru import logger
from pydantic import BaseModel


class SystemConfig(BaseModel):
    """Persistent global program state for basic coordination and easy access to .env contents."""

    db_url: str
    config_path: Path = Path("./config.toml")
    invoked_command: str | None = None
    start_time: datetime = datetime.now(UTC)
    running: bool = True
    scheduler_mode: str = "unspecified"
    log_level: str = "INFO"
    log_all_sql: bool = False
    tick_rate: float = 0.01
    max_workers_per_pool: int = 32
    minimum_workers_per_pool: int = 3

    class Config:
        extra = "ignore"  # ignore unknown keys if loading from larger env dict


def hydrate_system_config(env_path: Path = Path(".env")) -> SystemConfig:
    """Generates a system config using a .env file"""
    raw_env = dotenv_values(env_path)
    env = {k.casefold(): v for k, v in raw_env.items() if v is not None}
    return SystemConfig.model_validate(env)


def store_system_config(env_path: Path = Path(".env")) -> None:
    """Writes a system config bck to a .env file"""
    config = system_config.model_dump()
    logger.info(f"Stored global config: {config}")
    blacklist = {"running", "invoked_command", "start_time"}
    cleaned = {key: str(value) for key, value in config.items() if key not in blacklist}

    # Merge with existing env values
    existing = dotenv_values(env_path)
    updated = {**existing, **cleaned}

    with env_path.open("w") as env_file:
        for key, value in updated.items():
            env_file.write(f"{key}={value}\n")


def update_system_config(new_config: SystemConfig):
    """helper function for modules to use for pushing an updated system state to the rest of the program"""
    global system_config  # noqa: PLW0603
    system_config = new_config
    store_system_config()


__version__ = "0.0.0"
system_config: SystemConfig = hydrate_system_config()
