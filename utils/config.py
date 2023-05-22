import os
from functools import lru_cache

from pydantic import BaseSettings, PostgresDsn


class Settings(BaseSettings):
    asyncpg_url: PostgresDsn = PostgresDsn.build(
        scheme="postgresql+asyncpg",
        user="postgres",
        password="postgres",
        host="db",
        port="5432",
        path=f"/kefir_db",
    )


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
