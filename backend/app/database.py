import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

raw_db_url = os.getenv("DATABASE_URL")

if not raw_db_url:
    # Resolve robust absolute path to rubrimark.db in backend
    here = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(here)
    backend_db = os.path.join(backend_dir, "rubrimark.db")
    root_db = os.path.join(os.path.dirname(backend_dir), "rubrimark.db")
    
    if os.path.exists(backend_db):
        target_db = backend_db
    elif os.path.exists(root_db):
        target_db = root_db
    else:
        target_db = backend_db
        
    DATABASE_URL = f"sqlite:///{target_db.replace(os.sep, '/')}"
else:
    DATABASE_URL = raw_db_url

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
