from datetime import UTC, datetime
from pathlib import Path

from dotenv import dotenv_values
from pydantic import BaseModel


class SystemConfig(BaseModel):
    db_url: str
    config_path: Path = Path("./config.toml")
    invoked_command: str | None = None
    start_time: datetime = datetime.now(UTC)
    running: bool = True
    scheduler_mode: str = "unspecified"
    log_level: str = "INFO"
    class Config:
        extra = "ignore"  # ignore unknown keys if loading from larger env dict


    
def hydrate_system_config(env_path: Path = Path(".env")) -> SystemConfig:
    raw_env = dotenv_values(env_path)
    env = {k.casefold(): v for k, v in raw_env.items() if v is not None}
    return SystemConfig.model_validate(env)

def store_system_config(env_path: Path = Path(".env")) -> None:
    config = system_config.model_dump()
    blacklist = {"running", "invoked_command", "start_time"}
    cleaned = {key: str(value) for key, value in config.items() if key not in blacklist}

    # Merge with existing env values
    existing = dotenv_values(env_path)
    updated = {**existing, **cleaned}

    with env_path.open("w") as env_file:
        for key, value in updated.items():
            env_file.write(f"{key}={value}\n")

def update_system_config(new_config: SystemConfig):
    global system_config  # noqa: PLW0603
    system_config = new_config
    store_system_config()

__version__ = "0.0.0"
system_config: SystemConfig = hydrate_system_config()

