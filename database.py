from sqlmodel import create_engine, SQLModel, Session, select
from models import User, Problem, UserProgress
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./leet_amigos.db")

# Create engine with appropriate settings for SQLite vs PostgreSQL
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # PostgreSQL configuration
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


def init_db():
    create_db_and_tables()
    
    # Create admin user if it doesn't exist
    with Session(engine) as session:
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin = session.exec(
            select(User).where(User.username == admin_username)
        ).first()
        
        if not admin:
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
            admin_user = User(
                username=admin_username,
                password_hash=pwd_context.hash(admin_password),
                is_admin=True
            )
            session.add(admin_user)
            session.commit()
            print(f"Admin user created: username={admin_username}, password={admin_password}")


if __name__ == "__main__":
    init_db()