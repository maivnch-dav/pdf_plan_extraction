from sqlalchemy import String, Text, Float, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), default="Demo User")
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, default="demo@taskflow.local")
    documents: Mapped[list["Document"]] = relationship(back_populates="user")

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    file_name: Mapped[str] = mapped_column(String(255))
    raw_text: Mapped[str] = mapped_column(Text)
    user: Mapped["User"] = relationship(back_populates="documents")
    people: Mapped[list["Person"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    tasks: Mapped[list["Task"]] = relationship(back_populates="document", cascade="all, delete-orphan")

class Person(Base):
    __tablename__ = "people"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(255), default="")
    document: Mapped["Document"] = relationship(back_populates="people")
    tasks: Mapped[list["Task"]] = relationship(back_populates="person", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id"))
    external_id: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    due_date: Mapped[str] = mapped_column(String(120), default="")
    project: Mapped[str] = mapped_column(String(255), default="")
    source_text: Mapped[str] = mapped_column(Text, default="")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    document: Mapped["Document"] = relationship(back_populates="tasks")
    person: Mapped["Person"] = relationship(back_populates="tasks")
