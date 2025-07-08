from sqlmodel import create_engine, SQLModel, Session, select
from models import User, Problem, UserProgress
from passlib.context import CryptContext

# Database configuration
DATABASE_URL = "sqlite:///./leet_amigos.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


def init_db():
    create_db_and_tables()
    
    # Create admin user if it doesn't exist
    with Session(engine) as session:
        admin = session.exec(
            select(User).where(User.username == "admin")
        ).first()
        
        if not admin:
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            admin_user = User(
                username="admin",
                password_hash=pwd_context.hash("admin123"),
                is_admin=True
            )
            session.add(admin_user)
            session.commit()
            print("Admin user created: username=admin, password=admin123")


if __name__ == "__main__":
    init_db()