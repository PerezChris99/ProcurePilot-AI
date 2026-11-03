from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import get_settings

class Base(DeclarativeBase):
    pass

def _engine_options(database_url: str) -> dict:
    if database_url.startswith('sqlite'):
        return {'connect_args': {'check_same_thread': False}}
    return {'pool_pre_ping': True, 'pool_recycle': 300}

engine=create_engine(get_settings().database_url,**_engine_options(get_settings().database_url))
SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False)

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()
