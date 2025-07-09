from sqlalchemy import create_engine
from models import Base
from config import Config

def create_tables():
    engine = create_engine(Config.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")

def init_database():
    try:
        Config.validate()
        create_tables()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    init_database()