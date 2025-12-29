import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, validator
from typing import Optional

Base = declarative_base()

class DBAgent(Base):
    __tablename__ = "agents"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    module = Column(String, nullable=True)
    sub_module = Column(String, nullable=True)
    role = Column(String, nullable=False)
    status = Column(String, default="draft")  # draft, deployed, active, disabled
    temperature = Column(String, nullable=True)  # e.g., "0.7"
    max_tokens = Column(String, nullable=True)  # e.g., "4096"
    system_prompt = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DBRun(Base):
    __tablename__ = "agent_runs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, ForeignKey("agents.id"))
    status = Column(String, default="started")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DBTask(Base):
    __tablename__ = "agent_tasks"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("agent_runs.id"))
    description = Column(Text, nullable=False)
    status = Column(String, default="queued")
    result = Column(Text, nullable=True) # Logging Result
    error = Column(Text, nullable=True)  # Logging Error
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DBReflection(Base):
    __tablename__ = "agent_reflections" # Episodic Memory
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("agent_runs.id"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DBFeedback(Base):
    __tablename__ = "agent_feedback"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("agent_runs.id"))
    rating = Column(String, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# API Schemas
class AgentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    module: Optional[str] = None
    sub_module: Optional[str] = None
    role: str
    temperature: Optional[str] = None
    max_tokens: Optional[str] = None
    system_prompt: Optional[str] = None

class AgentUpdate(BaseModel):
    status: str

    @validator('status')
    def status_must_be_valid(cls, v):
        allowed_statuses = ["draft", "deployed", "active", "disabled"]
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of {allowed_statuses}')
        return v

class TaskUpdate(BaseModel):
    status: str
    result: Optional[str] = None
    error: Optional[str] = None

class ReflectionCreate(BaseModel):
    content: str

# Response Models
class AgentResponse(BaseModel):
    agent_id: str
    name: str
    description: Optional[str] = None
    module: Optional[str] = None
    sub_module: Optional[str] = None
    status: str
    created_at: str
    temperature: Optional[str] = None
    max_tokens: Optional[str] = None
    system_prompt: Optional[str] = None

class RunResponse(BaseModel):
    id: str
    agent_id: str
    status: str
    created_at: str

class TaskResponse(BaseModel):
    id: str
    run_id: str
    description: str
    status: str
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: str

class ReflectionResponse(BaseModel):
    id: str
    run_id: str
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
    id: str
    run_id: str
    rating: int
    comment: Optional[str] = None
    created_at: str

class RunStartResponse(BaseModel):
    run: RunResponse
    task: TaskResponse