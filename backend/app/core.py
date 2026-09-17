from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
 model_config=SettingsConfigDict(env_file='.env',extra='ignore')
 secret_key:str='development-only-change-me'; database_url:str='sqlite:///./noticelens.db'; cors_origins:str='http://localhost:5173'; upload_dir:str='uploads'
settings=Settings(); Path(settings.upload_dir).mkdir(parents=True,exist_ok=True)
