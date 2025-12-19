<<<<<<< HEAD
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from database import get_db
from models import DBAgent, DBRun, DBTask, AgentCreate

app = FastAPI(title="Agent API")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/agents")
def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    try:
        new_agent = DBAgent(name=agent.name, role=agent.role)
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        return new_agent
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents")
def get_agents(db: Session = Depends(get_db)):
    return db.query(DBAgent).all()

# Stub endpoints for UI matching
@app.post("/agents/{agent_id}/run")
def start_run(agent_id: uuid.UUID, db: Session = Depends(get_db)):
    new_run = DBRun(agent_id=agent_id, status="started")
    db.add(new_run)
    db.commit()
    db.refresh(new_run)
    return new_run

@app.get("/runs/{id}")
def get_run(id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(DBRun).filter(DBRun.id == id).first()
=======
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from database import get_db
from models import DBAgent, DBRun, DBTask, DBReflection, AgentCreate, TaskUpdate, ReflectionCreate

app = FastAPI(title="Agent API")

@app.get("/health")
def health_check():
    return {"status": "healthy"}

# --- AGENTS ---
@app.post("/agents")
def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    try:
        new_agent = DBAgent(name=agent.name, role=agent.role)
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        return new_agent
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents")
def get_agents(db: Session = Depends(get_db)):
    return db.query(DBAgent).all()

# --- RUNS ---
@app.post("/agents/{agent_id}/run")
def start_run(agent_id: uuid.UUID, db: Session = Depends(get_db)):
    new_run = DBRun(agent_id=agent_id, status="started")
    db.add(new_run)
    db.commit()
    db.refresh(new_run)
    return new_run

# --- TASKS (Logging Layer) ---
@app.patch("/tasks/{task_id}")
def update_task(task_id: uuid.UUID, data: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(DBTask).filter(DBTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.status = data.status
    if data.result: task.result = data.result
    if data.error: task.error = data.error
    
    db.commit()
    db.refresh(task)
    return task

# --- REFLECTIONS (Memory Layer) ---
@app.post("/runs/{run_id}/reflections")
def add_reflection(run_id: uuid.UUID, reflection: ReflectionCreate, db: Session = Depends(get_db)):
    new_reflection = DBReflection(run_id=run_id, content=reflection.content)
    db.add(new_reflection)
    db.commit()
    db.refresh(new_reflection)
    return new_reflection
>>>>>>> 6decf83 (Memory & Logging Layer)
