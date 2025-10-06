from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, MySQLDsn, MariaDBDsn, AnyUrl, UrlConstraints


class SqliteDsn(AnyUrl):
    """A type that will accept any SQLite or AIOSQlite DSN.

    * File path required (e.g., `sqlite+aiosqlite:///database.db`).
    """

    _constraints = UrlConstraints(
        allowed_schemes=["sqlite", "aiosqlite", "sqlite+aiosqlite"],
        default_path="/database.db",
    )


class SAMConfig(BaseSettings):
    """Configuration for Script's Advanced Moderation."""

    database_uri: SqliteDsn | PostgresDsn | MySQLDsn | MariaDBDsn
    builtin_logger_enabled: bool = True

    class Config:
        env_file = ".env"
        env_prefix = "sam_"
        extra = "allow"

config = SAMConfig() # type: ignore

if __name__ == "__main__":
    print(config.model_dump())
