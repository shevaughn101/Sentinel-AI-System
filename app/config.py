from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./sentinel.db"
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-20b"
    free_daily_request_cap: int = 40
    free_monthly_request_cap: int = 500
    free_daily_input_token_cap: int = 40000
    free_monthly_input_token_cap: int = 250000
    max_input_tokens_per_request: int = 4000
    max_output_tokens: int = 800
    retrieval_chunks: int = 6
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
