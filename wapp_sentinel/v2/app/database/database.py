from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:admin@localhost:5432/napoleon-sentinel-db")

engine = create_engine(DATABASE_URL)

# Устанавливаем временную зону UTC для каждого подключения
@event.listens_for(engine, 'connect')
def set_timezone(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute('SET timezone TO "UTC"')
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
