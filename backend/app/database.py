from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase,sessionmaker
from .core import settings
def sqlalchemy_url(url: str) -> str:
 if url.startswith('postgres://'):
  return 'postgresql+psycopg://' + url.removeprefix('postgres://')
 if url.startswith('postgresql://'):
  return 'postgresql+psycopg://' + url.removeprefix('postgresql://')
 return url

database_url=sqlalchemy_url(settings.database_url)
engine=create_engine(database_url,connect_args={'check_same_thread':False} if database_url.startswith('sqlite') else {},pool_pre_ping=not database_url.startswith('sqlite'))
SessionLocal=sessionmaker(bind=engine,autoflush=False)
class Base(DeclarativeBase): pass
def get_db():
 db=SessionLocal()
 try: yield db
 finally: db.close()
