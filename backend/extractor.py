import json, os, re
from typing import Dict, Any, List
from dotenv import load_dotenv
load_dotenv()

TASK_SCHEMA = {"name":"taskflow_extraction","schema":{"type":"object","additionalProperties":False,"properties":{"people":{"type":"array","items":{"type":"object","additionalProperties":False,"properties":{"id":{"type":"string"},"name":{"type":"string"},"role":{"type":"string"},"tasks":{"type":"array","items":{"type":"object","additionalProperties":False,"properties":{"id":{"type":"string"},"title":{"type":"string"},"description":{"type":"string"},"due_date":{"type":"string"},"project":{"type":"string"},"source_text":{"type":"string"},"confidence_score":{"type":"number"}},"required":["id","title","description","due_date","project","source_text","confidence_score"]}}},"required":["id","name","role","tasks"]}}},"required":["people"]},"strict":True}

def slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-") or "item"

def mock_extract_tasks(raw_text: str) -> Dict[str, Any]:
    project_match = re.search(r"Project:\s*(.+)", raw_text)
    project = project_match.group(1).strip() if project_match else "Team Project"
    people: List[Dict[str, Any]] = []
    current = None
    for line in raw_text.splitlines():
        line = line.strip()
        if not line: continue
        person_match = re.match(r"^([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)+)\s+—\s+(.+)$", line)
        if person_match:
            name, role = person_match.group(1).strip(), person_match.group(2).strip()
            current = {"id": slug(name), "name": name, "role": role, "tasks": []}
            people.append(current); continue
        task_match = re.match(r"^-\s*(.+?)\s+—\s+due\s+(.+)$", line, flags=re.I)
        if task_match and current:
            title, due = task_match.group(1).strip(), task_match.group(2).strip()
            task_id = f"{current['id']}-{len(current['tasks'])+1}"
            current["tasks"].append({"id":task_id,"title":title[:1].upper()+title[1:],"description":f"{title} for {project}.","due_date":due,"project":project,"source_text":line,"confidence_score":0.88})
    if not people:
        people = [{"id":"demo-person","name":"Demo Person","role":"Team Member","tasks":[{"id":"demo-task-1","title":"Review uploaded schedule","description":"Fallback task generated because no clear structure was detected.","due_date":"To be confirmed","project":"Demo Project","source_text":raw_text[:200],"confidence_score":0.50}]}]
    return {"people": people}

def extract_tasks(raw_text: str) -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    if not api_key: return mock_extract_tasks(raw_text)
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    prompt = "Extract people, roles, tasks, deadlines, projects, source text, and confidence scores from this schedule. Do not invent data.\n\n" + raw_text
    response = client.chat.completions.create(
        model=model,
        messages=[{"role":"system","content":"You convert messy team schedules into structured task data."},{"role":"user","content":prompt}],
        response_format={"type":"json_schema","json_schema":TASK_SCHEMA},
    )
    return json.loads(response.choices[0].message.content)
