from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# SQLite configuration with concurrency safeguards
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30}
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_database_schema():
    """Ensures newly added columns exist in the SQLite database tables."""
    try:
        with engine.connect() as conn:
            cursor = conn.connection.cursor()
            cursor.execute("PRAGMA table_info(rubrics)")
            cols = [c[1] for c in cursor.fetchall()]
            if cols:
                if "generation_mode" not in cols:
                    cursor.execute("ALTER TABLE rubrics ADD COLUMN generation_mode VARCHAR(64) DEFAULT 'rule_based'")
                if "rag_context_used" not in cols:
                    cursor.execute("ALTER TABLE rubrics ADD COLUMN rag_context_used TEXT")

            cursor.execute("PRAGMA table_info(assessments)")
            a_cols = [c[1] for c in cursor.fetchall()]
            if a_cols:
                if "learning_outcome" not in a_cols:
                    cursor.execute("ALTER TABLE assessments ADD COLUMN learning_outcome TEXT")
                if "lecturer_guidelines" not in a_cols:
                    cursor.execute("ALTER TABLE assessments ADD COLUMN lecturer_guidelines TEXT")

            conn.connection.commit()
    except Exception as e:
        print(f"Database schema auto-migration notice: {e}")


ensure_database_schema()
