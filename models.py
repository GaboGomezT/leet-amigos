from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List
from enum import Enum


class DifficultyEnum(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    progress: List["UserProgress"] = Relationship(back_populates="user")


class Problem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    url: str = Field(unique=True, index=True)  # Make URL unique to prevent duplicates
    solution_url: Optional[str] = None
    difficulty: DifficultyEnum
    category: Optional[str] = None  # Supertopic or general theme
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user_progress: List["UserProgress"] = Relationship(back_populates="problem")


class UserProgress(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    problem_id: int = Field(foreign_key="problem.id")
    is_solved: bool = Field(default=False)
    solved_at: Optional[datetime] = None
    month_year: str = Field(index=True)  # Format: "2024-07" for July 2024
    
    # Relationships
    user: User = Relationship(back_populates="progress")
    problem: Problem = Relationship(back_populates="user_progress")


# Pydantic models for API
class UserCreate(SQLModel):
    username: str
    password: str


class UserLogin(SQLModel):
    username: str
    password: str


class ProblemCreate(SQLModel):
    title: str
    url: str
    solution_url: Optional[str] = None
    difficulty: DifficultyEnum
    category: Optional[str] = None


class ProblemUpdate(SQLModel):
    title: Optional[str] = None
    url: Optional[str] = None
    solution_url: Optional[str] = None
    difficulty: Optional[DifficultyEnum] = None
    category: Optional[str] = None


class ProgressUpdate(SQLModel):
    problem_id: int
    is_solved: bool