import os
import sys


class Settings:
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "taskflow")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "taskflow_secret")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "taskflow")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "db")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")

    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRY_HOURS: int = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

    def __init__(self):
        jwt_secret = os.getenv("JWT_SECRET")
        if not jwt_secret:
            print("FATAL: JWT_SECRET environment variable is not set. Exiting.", file=sys.stderr)
            sys.exit(1)
        self.JWT_SECRET: str = jwt_secret

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
