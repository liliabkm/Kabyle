import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://kabyle:kabyle_local@127.0.0.1:5432/kabyle")
engine = create_engine(DATABASE_URL, **({"connect_args": {"check_same_thread": False}} if DATABASE_URL.startswith("sqlite") else {}))
Session = sessionmaker(engine)
class Base(DeclarativeBase): pass
