import os


class Settings:
    INTERNAL_API_KEY: str = os.getenv("INTERNAL_API_KEY", "")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://pydocai_user:pydocai_pass@localhost:5433/pydocai"
    )
    CORS_ALLOWED_ORIGINS: str = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173")


settings = Settings()
