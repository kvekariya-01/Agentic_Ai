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