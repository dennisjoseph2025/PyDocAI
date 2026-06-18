import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String(254), nullable=False)


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    status = Column(String(20), default="pending")
    source_type = Column(String(20), default="file")
    file_name = Column(String(255), default="", server_default="")
    file_size = Column(Integer, nullable=True)
    github_url = Column(String(500), nullable=True)
    github_branch = Column(String(100), default="main")
    parsed_data = Column(JSON, nullable=True)
    generated_docs = Column(Text, nullable=True)
    readme_docs = Column(Text, nullable=True)
    api_docs = Column(Text, nullable=True)
    project_info = Column(JSON, nullable=True)
    custom_details = Column(JSON, nullable=True)
    framework_info = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    files = relationship("ProjectFile", back_populates="project")


class ProjectFile(Base):
    __tablename__ = "project_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=True)
    content = Column(Text, default="")
    parsed_data = Column(JSON, nullable=True)
    generated_docs = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="files")
