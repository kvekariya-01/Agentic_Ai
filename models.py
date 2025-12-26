import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import Optional

Base = declarative_base()

class DBAgent(Base):
    __tablename__ = "agents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DBRun(Base):
    __tablename__ = "agent_runs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id"))
    status = Column(String, default="started")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DBTask(Base):
    __tablename__ = "agent_tasks"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id"))
    description = Column(Text, nullable=False)
    status = Column(String, default="queued")
    result = Column(Text, nullable=True) # Logging Result
    error = Column(Text, nullable=True)  # Logging Error
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DBReflection(Base):
    __tablename__ = "agent_reflections" # Episodic Memory
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DBFeedback(Base):
    __tablename__ = "agent_feedback"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("agent_runs.id"))
    rating = Column(String, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# API Schemas
class AgentCreate(BaseModel):
    name: str
    role: str

class TaskUpdate(BaseModel):
    status: str
    result: Optional[str] = None
    error: Optional[str] = None

class ReflectionCreate(BaseModel):
    content: str

# Response Models
class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    role: str
    created_at: str

class RunResponse(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    status: str
    created_at: str

class TaskResponse(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    description: str
    status: str
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: str

class ReflectionResponse(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    content: str
    created_at: str

class RunTraceResponse(BaseModel):
    run: RunResponse
    tasks: list[TaskResponse]
    reflections: list[ReflectionResponse]

class FeedbackCreate(BaseModel):
    rating: int
    comment: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    rating: int
    comment: Optional[str] = None
    created_at: str

class RunStartResponse(BaseModel):
    run: RunResponse
    task: TaskResponse