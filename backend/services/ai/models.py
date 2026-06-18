import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String(254), nullable=False)


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    status = Column(String(20), default="pending")
    source_type = Column(String(20), default="file")
    github_url = Column(String(500), nullable=True)
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


class ProjectFile(Base):
    __tablename__ = "project_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    content = Column(Text, default="")
    parsed_data = Column(JSON, nullable=True)
    generated_docs = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CodeEmbedding(Base):
    __tablename__ = "code_embeddings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    chunk_type = Column(String(20), nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(384), nullable=False)
    chunk_metadata = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
