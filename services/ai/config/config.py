import os


class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_API_KEY_2: str = os.getenv("GROQ_API_KEY_2", "")
    INTERNAL_API_KEY: str = os.getenv("INTERNAL_API_KEY", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://pydocai_user:pydocai_pass@localhost:5433/pydocai"
    )
    CORS_ALLOWED_ORIGINS: str = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173")


settings = Settings()
