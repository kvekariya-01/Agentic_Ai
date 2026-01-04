from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse  # Added for redirection
from sqlalchemy.orm import Session
import logging
import os
import uuid
from database import get_db
from models import (
    DBAgent, DBRun, DBTask, DBReflection, DBFeedback,
    AgentCreate, AgentUpdate, TaskUpdate, ReflectionCreate, FeedbackCreate,
    AgentResponse, RunResponse, TaskResponse, ReflectionResponse,
    RunTraceResponse, FeedbackResponse, RunStartResponse
)
from policy_middleware import PolicyMiddleware

app = FastAPI(title="Agent API - Memory & Logging")

# Initialize policy middleware
policy_path = os.getenv("POLICY_PATH", "./agent_policy.yaml")
policy_middleware = PolicyMiddleware(policy_path)

# --- NEW REDIRECT ROUTE ---
@app.get("/", include_in_schema=False)
async def docs_redirect():
    """Redirects the root URL to the interactive documentation."""
    return RedirectResponse(url="/docs")

@app.get("/health")
def health_check():
    return {"status": "healthy"}
@app.post("/agents", response_model=AgentResponse)
def create_agent(agent: AgentCreate, db: Session = Depends(get_db)):
    try:
        # 1. Create the database object using the input data
        new_agent = DBAgent(
            name=agent.name,
            description=agent.description,
            module=agent.module,
            sub_module=agent.sub_module,
            role=agent.role,
            temperature=agent.temperature or 0.7, # Default if None
            max_tokens=agent.max_tokens or 2000,   # Default if None
            system_prompt=agent.system_prompt
        )
        
        db.add(new_agent)
        db.commit()
        db.refresh(new_agent)
        
        # 2. Return the object directly
        # Pydantic will handle the conversion to AgentResponse automatically
        # as long as you have 'from_attributes = True' in your schema.
        return new_agent
        
    except Exception as e:
        db.rollback()
        logging.error(f"HF Deployment Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")

@app.get("/agents", response_model=list[AgentResponse])
def get_agents(status: str = None, db: Session = Depends(get_db)):
    query = db.query(DBAgent)
    if status:
        query = query.filter(DBAgent.status == status)
    agents = query.all()
    return agents


@app.get("/agents/deployed", response_model=list[AgentResponse])
def get_deployed_agents(db: Session = Depends(get_db)):
    agents = db.query(DBAgent).filter(DBAgent.status == "deployed").all()
    return [
        AgentResponse(
            agent_id=agent.id,
            name=agent.name,
            description=agent.description,
            module=agent.module,
            sub_module=agent.sub_module,
            status=agent.status,
            created_at=agent.created_at.isoformat(),
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            system_prompt=agent.system_prompt
        ) for agent in agents
    ]

@app.patch("/agents/{agent_id}", response_model=AgentResponse)
def update_agent(agent_id: str, agent_update: AgentUpdate, db: Session = Depends(get_db)):
    # 1. Validate UUID
    try:
        agent_uuid = uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid agent_id format")

    # 2. Query using UUID
    agent = db.query(DBAgent).filter(DBAgent.id == agent_uuid).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # 3. Update fields (safe update)
    if agent_update.status is not None:
        agent.status = agent_update.status

    db.commit()
    db.refresh(agent)

    return agent

@app.post("/agents/{agent_id}/run", response_model=RunStartResponse)
def start_run(agent_id: str, db: Session = Depends(get_db)):
    try:
        agent_uuid = uuid.UUID(agent_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid agent_id format")

    agent = db.query(DBAgent).filter(DBAgent.id == agent_uuid).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    new_run = DBRun(agent_id=agent_uuid, status="started")
    db.add(new_run)
    db.commit()
    db.refresh(new_run)

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

@app.patch("/tasks/{task_id}")
def update_task(task_id: str, data: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(DBTask).filter(DBTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = data.status
    if data.result: task.result = data.result
    if data.error: task.error = data.error
    db.commit()
    return task

@app.post("/runs/{run_id}/reflections", response_model=ReflectionResponse)
def add_reflection(run_id: str, reflection: ReflectionCreate, db: Session = Depends(get_db)):
    logging.info(f"Adding reflection for run_id: {run_id}")
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

@app.get("/runs/{run_id}", response_model=RunResponse)
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(DBRun).filter(DBRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return RunResponse(
        id=run.id,
        agent_id=run.agent_id,
        status=run.status,
        created_at=run.created_at.isoformat()
    )

@app.get("/runs/{run_id}/trace", response_model=RunTraceResponse)
def get_run_trace(run_id: str, db: Session = Depends(get_db)):
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

@app.post("/runs/{run_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(run_id: str, feedback: FeedbackCreate, db: Session = Depends(get_db)):
    run = db.query(DBRun).filter(DBRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    new_feedback = DBFeedback(run_id=run_id, rating=feedback.rating, comment=feedback.comment)
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

@app.get("/audit-log")
def get_audit_log(filter_violations: bool = False):
    return {"audit_log": policy_middleware.get_audit_log(filter_violations)}

@app.get("/rate-limits")
def get_rate_limits():
    return policy_middleware.get_rate_limit_status()

@app.get("/metrics")
def get_metrics():
    return {
        "total_runs": 0,
        "successful_runs": 0,
        "average_latency": 0.0,
        "success_score": 0.0
    }

@app.post("/governance/override")
def manual_override(action: str, module: str, reason: str):
    policy_middleware.audit_log.append(f"[MANUAL OVERRIDE] {action} in {module} - Reason: {reason}")
    return {"status": "override_granted"}

@app.post("/governance/approve-action")
def approve_action(action: str, module: str, approved: bool):
    if approved:
        policy_middleware.audit_log.append(f"[APPROVAL GRANTED] {action} in {module}")
        return {"status": "approved"}
    else:
        policy_middleware.audit_log.append(f"[APPROVAL DENIED] {action} in {module}")
        return {"status": "denied"}