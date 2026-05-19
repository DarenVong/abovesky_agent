from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    ollama_url: str = "http://ollama:11434"
    default_model: str = "claude-sonnet-4-6"
    db_path: str = "/data/abovesky.db"

    model_config = {"env_file": ".env"}


settings = Settings()
