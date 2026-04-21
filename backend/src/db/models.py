from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from src.core.config import config

Base = declarative_base()

class GlossaryEntryDB(Base):
    __tablename__ = 'glossary_entries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    original = Column(String(500), unique=True, nullable=False, index=True)
    translation = Column(String(500), nullable=False)
    entity_type = Column(String(50), default='person')
    aliases = Column(Text, default='[]')
    locked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TranslationTaskDB(Base):
    __tablename__ = 'translation_tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(100), unique=True, nullable=False, index=True)
    filename = Column(String(500))
    source_language = Column(String(50), default='Chinese')
    target_language = Column(String(50), default='English')
    status = Column(String(50), default='pending')
    current_chapter = Column(Integer, default=0)
    total_chapters = Column(Integer, default=0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

engine = create_engine(config.DATABASE_URL.replace('sqlite:///', 'sqlite:///'))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
