#!/usr/bin/env python3
"""
Sample Data Seeding Script for Agent API
This script creates sample data to validate UI compatibility
"""

import uuid
import sys
import os
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import DBAgent, DBRun, DBTask, DBReflection, DBFeedback

def seed_sample_data():
    """Create sample data for testing the API"""
    
    # Create database session
    db = SessionLocal()
    
    try:
        print("Starting data seeding...")
        
        # Clear existing data (optional - comment out if you want to preserve data)
        print("Clearing existing data...")
        db.query(DBFeedback).delete()
        db.query(DBReflection).delete()
        db.query(DBTask).delete()
        db.query(DBRun).delete()
        db.query(DBAgent).delete()
        db.commit()
        print("Existing data cleared")
        
        # Create sample agents
        print("Creating sample agents...")
        agents = [
            DBAgent(name="Data Analysis Agent", role="Analyze datasets and generate insights"),
            DBAgent(name="Code Review Agent", role="Review code for quality and security"),
            DBAgent(name="Content Writer Agent", role="Create engaging content for various topics")
        ]
        
        for agent in agents:
            db.add(agent)
        db.commit()
        
        # Refresh agents to get their IDs
        for agent in agents:
            db.refresh(agent)
        
        print(f"Created {len(agents)} agents")
        
        # Create sample runs for each agent
        print("Creating sample runs...")
        runs = []
        
        for agent_idx, agent in enumerate(agents):
            # Create 2-3 runs per agent
            for i in range(2 + (agent_idx % 2)):  # 2-3 runs per agent
                status = "completed" if i > 0 else "running"
                run = DBRun(agent_id=agent.id, status=status)
                db.add(run)
                runs.append(run)
        
        db.commit()
        
        # Refresh runs to get their IDs
        for run in runs:
            db.refresh(run)
        
        print(f"Created {len(runs)} runs")
        
        # Create sample tasks for each run
        print("Creating sample tasks...")
        tasks = []
        
        for run in runs:
            # Create 3-5 tasks per run
            task_count = 3 + (hash(str(run.id)) % 3)  # 3-5 tasks
            for i in range(task_count):
                if run.status == "completed":
                    status = "completed" if i < task_count - 1 else "completed"
                    result = f"Task {i+1} completed successfully with analysis results"
                elif run.status == "running":
                    status = "completed" if i < 2 else "in_progress"
                    result = f"Task {i+1} completed successfully" if i < 2 else None
                else:
                    status = "queued"
                    result = None
                
                error = None if status != "failed" else f"Error in task {i+1}: Failed to process data"
                
                task = DBTask(
                    run_id=run.id,
                    description=f"Execute task {i+1}: {get_task_description(run.agent_id, i+1)}",
                    status=status,
                    result=result,
                    error=error
                )
                db.add(task)
                tasks.append(task)
        
        db.commit()
        
        # Refresh tasks to get their IDs
        for task in tasks:
            db.refresh(task)
        
        print(f"Created {len(tasks)} tasks")
        
        # Create sample reflections for each run
        print("Creating sample reflections...")
        reflections = []
        
        for run in runs:
            # Create 1-3 reflections per run
            reflection_count = 1 + (hash(str(run.id)) % 3)
            for i in range(reflection_count):
                reflection = DBReflection(
                    run_id=run.id,
                    content=f"Reflection {i+1}: {get_reflection_content(run.agent_id, i+1)}"
                )
                db.add(reflection)
                reflections.append(reflection)
        
        db.commit()
        
        # Refresh reflections to get their IDs
        for reflection in reflections:
            db.refresh(reflection)
        
        print(f"Created {len(reflections)} reflections")
        
        # Create sample feedback for completed runs
        print("Creating sample feedback...")
        feedback_count = 0
        
        for run in runs:
            if run.status == "completed" and hash(str(run.id)) % 2 == 0:  # 50% of completed runs
                rating = 3 + (hash(str(run.id)) % 3)  # Rating 3-5
                comment = get_feedback_comment(rating)
                
                feedback = DBFeedback(
                    run_id=run.id,
                    rating=str(rating),
                    comment=comment
                )
                db.add(feedback)
                feedback_count += 1
        
        db.commit()
        print(f"Created {feedback_count} feedback entries")
        
        # Print summary
        print("\nData Seeding Summary:")
        print(f"   Agents: {len(agents)}")
        print(f"   Runs: {len(runs)}")
        print(f"   Tasks: {len(tasks)}")
        print(f"   Reflections: {len(reflections)}")
        print(f"   Feedback: {feedback_count}")
        
        print("\nSample data seeding completed successfully!")
        print("\nSample Data Overview:")
        
        # Print sample data for verification
        for agent in agents:
            agent_runs = [r for r in runs if r.agent_id == agent.id]
            print(f"\nAgent: {agent.name} ({agent.role})")
            print(f"   Runs: {len(agent_runs)}")
            
            for run in agent_runs:
                run_tasks = [t for t in tasks if t.run_id == run.id]
                run_reflections = [r for r in reflections if r.run_id == run.id]
                print(f"   ├── Run: {run.status} ({len(run_tasks)} tasks, {len(run_reflections)} reflections)")
        
        return True
        
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

def get_task_description(agent_id, task_num):
    """Get task description based on agent type and task number"""
    descriptions = {
        1: ["Load and validate dataset", "Perform data quality checks", "Clean missing values"],
        2: ["Review code syntax", "Check security vulnerabilities", "Analyze code complexity"],
        3: ["Research topic keywords", "Create content outline", "Write engaging content"]
    }
    
    agent_type = (hash(str(agent_id)) % 3) + 1
    agent_descriptions = descriptions.get(agent_type, descriptions[1])
    return agent_descriptions[(task_num - 1) % len(agent_descriptions)]

def get_reflection_content(agent_id, reflection_num):
    """Get reflection content based on agent type"""
    reflections = {
        1: ["Successfully identified data patterns and anomalies", "Learned optimal cleaning strategies for this dataset type"],
        2: ["Code quality has improved with these review patterns", "Security vulnerabilities were properly addressed"],
        3: ["Content engagement increased with this writing style", "Keyword research provided valuable insights"]
    }
    
    agent_type = (hash(str(agent_id)) % 3) + 1
    agent_reflections = reflections.get(agent_type, reflections[1])
    return agent_reflections[(reflection_num - 1) % len(agent_reflections)]

def get_feedback_comment(rating):
    """Get feedback comment based on rating"""
    comments = {
        3: "Good performance, room for improvement",
        4: "Excellent work, met expectations well",
        5: "Outstanding performance, exceeded expectations"
    }
    return comments.get(rating, "Satisfactory performance")

if __name__ == "__main__":
    success = seed_sample_data()
    sys.exit(0 if success else 1)