from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    supabase_url: str
    supabase_service_key: str
    cors_origins: str = "http://localhost:3000"
    chroma_db_path: str = "./chroma_db"
    notion_api_key: str = ""
    google_calendar_credentials_path: str = "../mcp-servers/google-calendar/credentials.json"

    class Config:
        env_file = ".env"


settings = Settings()
