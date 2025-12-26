from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
import logging
from database import get_db
from models import (
    DBAgent, DBRun, DBTask, DBReflection, DBFeedback,
    AgentCreate, TaskUpdate, ReflectionCreate, FeedbackCreate,
    AgentResponse, RunResponse, TaskResponse, ReflectionResponse,
    RunTraceResponse, FeedbackResponse, RunStartResponse
)

app = FastAPI(title="Agent API - Memory & Logging")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/agents")
def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    new_agent = DBAgent(name=agent.name, role=agent.role)
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    return new_agent

@app.post("/agents/{agent_id}/run", response_model=RunStartResponse)
def start_run(agent_id: uuid.UUID, db: Session = Depends(get_db)):
    new_run = DBRun(agent_id=agent_id, status="started")
    db.add(new_run)
    db.commit()
    db.refresh(new_run)

    # Create initial task
    new_task = DBTask(run_id=new_run.id, description="Execute agent run tasks")
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return RunStartResponse(
        run=RunResponse(
            id=new_run.id,
            agent_id=new_run.agent_id,
            status=new_run.status,
            created_at=new_run.created_at.isoformat()
        ),
        task=TaskResponse(
            id=new_task.id,
            run_id=new_task.run_id,
            description=new_task.description,
            status=new_task.status,
            result=new_task.result,
            error=new_task.error,
            created_at=new_task.created_at.isoformat()
        )
    )

# Endpoint to update Task Result (Logging)
@app.patch("/tasks/{task_id}")
def update_task(task_id: uuid.UUID, data: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(DBTask).filter(DBTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = data.status
    if data.result: task.result = data.result
    if data.error: task.error = data.error
    db.commit()
    return task

# Endpoint to add Reflection (Memory)
@app.post("/runs/{run_id}/reflections", response_model=ReflectionResponse)
def add_reflection(run_id: uuid.UUID, reflection: ReflectionCreate, db: Session = Depends(get_db)):
    logging.info(f"Adding reflection for run_id: {run_id}")
    # Verify run exists
    run = db.query(DBRun).filter(DBRun.id == run_id).first()
    if not run:
        logging.error(f"Run not found for run_id: {run_id}")
        raise HTTPException(status_code=404, detail="Run not found")

    logging.info(f"Run found: {run.id}")
    new_ref = DBReflection(run_id=run_id, content=reflection.content)
    db.add(new_ref)
    db.commit()
    db.refresh(new_ref)
    logging.info(f"Reflection added: {new_ref.id}")
    return ReflectionResponse(
        id=new_ref.id,
        run_id=new_ref.run_id,
        content=new_ref.content,
        created_at=new_ref.created_at.isoformat()
    )

# Endpoint to fetch all runs
@app.get("/runs", response_model=list[RunResponse])
def get_runs(db: Session = Depends(get_db)):
    runs = db.query(DBRun).all()
    return [
        RunResponse(
            id=run.id,
            agent_id=run.agent_id,
            status=run.status,
            created_at=run.created_at.isoformat()
        ) for run in runs
    ]

# Endpoint to fetch a specific run
@app.get("/runs/{run_id}", response_model=RunResponse)
def get_run(run_id: uuid.UUID, db: Session = Depends(get_db)):
    run = db.query(DBRun).filter(DBRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunResponse(
        id=run.id,
        agent_id=run.agent_id,
        status=run.status,
        created_at=run.created_at.isoformat()
    )

# Endpoint to fetch run trace (complete execution history)
@app.get("/runs/{run_id}/trace", response_model=RunTraceResponse)
def get_run_trace(run_id: uuid.UUID, db: Session = Depends(get_db)):
    run = db.query(DBRun).filter(DBRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    tasks = db.query(DBTask).filter(DBTask.run_id == run_id).all()
    reflections = db.query(DBReflection).filter(DBReflection.run_id == run_id).all()
    
    return RunTraceResponse(
        run=RunResponse(
            id=run.id,
            agent_id=run.agent_id,
            status=run.status,
            created_at=run.created_at.isoformat()
        ),
        tasks=[
            TaskResponse(
                id=task.id,
                run_id=task.run_id,
                description=task.description,
                status=task.status,
                result=task.result,
                error=task.error,
                created_at=task.created_at.isoformat()
            ) for task in tasks
        ],
        reflections=[
            ReflectionResponse(
                id=ref.id,
                run_id=ref.run_id,
                content=ref.content,
                created_at=ref.created_at.isoformat()
            ) for ref in reflections
        ]
    )

# Endpoint to submit feedback
@app.post("/runs/{run_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(run_id: uuid.UUID, feedback: FeedbackCreate, db: Session = Depends(get_db)):
    # Verify run exists
    run = db.query(DBRun).filter(DBRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    new_feedback = DBFeedback(run_id=run_id, rating=str(feedback.rating), comment=feedback.comment)
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)
    
    return FeedbackResponse(
        id=new_feedback.id,
        run_id=new_feedback.run_id,
        rating=int(new_feedback.rating),
        comment=new_feedback.comment,
        created_at=new_feedback.created_at.isoformat()
    )