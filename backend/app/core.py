import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
 model_config=SettingsConfigDict(env_file='.env',extra='ignore')
 secret_key:str='development-only-change-me'; database_url:str='sqlite:///./noticelens.db'; cors_origins:str=''; upload_dir:str='uploads'; session_cookie_secure:bool=False; session_cookie_samesite:str='lax'; tesseract_cmd:str|None=None
 @property
 def allowed_cors_origins(self) -> list[str]:
  required=('http://localhost:5173','https://notiq-wine.vercel.app')
  configured=tuple(origin.strip() for origin in self.cors_origins.split(',') if origin.strip())
  return list(dict.fromkeys((*required,*configured)))
 @property
 def is_render(self) -> bool:
  return bool(os.getenv('RENDER'))
settings=Settings(); Path(settings.upload_dir).mkdir(parents=True,exist_ok=True)


