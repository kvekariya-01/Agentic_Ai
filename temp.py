from database import SessionLocal
from models import DBAgent
db = SessionLocal()
agents = db.query(DBAgent).all()
print(f'Found {len(agents)} agents')
for a in agents:
    print(f'ID: {a.id}, Name: {a.name}, Role: {a.role}, Status: {a.status}, Temp: {a.temperature}, Tokens: {a.max_tokens}, Prompt: {a.system_prompt}, Created: {a.created_at}')
db.close()