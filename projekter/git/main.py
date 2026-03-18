"""
James PM — Local Project Management Tool
Start: python main.py
"""
import urllib.parse
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import get_project_dirs, get_project_color, BASE_PATH
from parser import parse_project_from_dir, ProjectData
from writer import (
    toggle_task,
    add_task_to_milestone,
    add_to_gtd_section,
    move_gtd_task,
    update_status_field,
    update_milestone_target,
    add_decision,
    update_task_text,
)

app = FastAPI(title="James PM")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _project_id_to_path(project_id: str) -> Optional[Path]:
    """Convert a URL-encoded project id (dir name) to a Path."""
    decoded = urllib.parse.unquote(project_id)
    for d in get_project_dirs():
        if d.name == decoded:
            return d
    return None


def _get_roadmap(project_id: str) -> tuple[Path, Path]:
    """Return (project_dir, roadmap_path). Raises 404 if not found."""
    proj_dir = _project_id_to_path(project_id)
    if proj_dir is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    roadmap = proj_dir / "ROADMAP.md"
    return proj_dir, roadmap


def _deadline_status(deadline: str) -> str:
    """Return 'critical', 'warning', or 'ok' based on deadline proximity."""
    import re
    from datetime import date
    m = re.search(r'(\d{4}-\d{2}-\d{2})', deadline)
    if not m:
        return 'ok'
    try:
        d = date.fromisoformat(m.group(1))
        delta = (d - date.today()).days
        if delta < 7:
            return 'critical'
        if delta < 14:
            return 'warning'
        return 'ok'
    except Exception:
        return 'ok'


# ─── HTML pages ───────────────────────────────────────────────────────────────

@app.get("/")
async def dashboard():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/gtd")
async def gtd_page():
    return FileResponse(STATIC_DIR / "gtd.html")


@app.get("/projekt/{project_id:path}")
async def project_page(project_id: str):
    return FileResponse(STATIC_DIR / "project.html")


# ─── API ──────────────────────────────────────────────────────────────────────

@app.get("/api/projects")
async def list_projects():
    """List all projects with summary data."""
    results = []
    for proj_dir in get_project_dirs():
        data = parse_project_from_dir(proj_dir)
        if data is None:
            continue
        d = data.to_dict()
        d["color"] = get_project_color(proj_dir.name)
        d["id"] = urllib.parse.quote(proj_dir.name)
        d["deadline_status"] = _deadline_status(d.get("next_deadline", ""))
        results.append(d)
    return JSONResponse(results)


@app.get("/api/projects/{project_id:path}")
async def get_project(project_id: str):
    """Get full project data."""
    proj_dir, _ = _get_roadmap(project_id)
    data = parse_project_from_dir(proj_dir)
    if data is None:
        raise HTTPException(status_code=404, detail="Could not parse project")
    d = data.to_dict()
    d["color"] = get_project_color(proj_dir.name)
    d["id"] = urllib.parse.quote(proj_dir.name)
    d["deadline_status"] = _deadline_status(d.get("next_deadline", ""))
    return JSONResponse(d)


class TaskToggle(BaseModel):
    line_index: int
    completed: bool


@app.put("/api/projects/{project_id:path}/task")
async def update_task(project_id: str, body: TaskToggle):
    _, roadmap = _get_roadmap(project_id)
    ok = toggle_task(roadmap, body.line_index, body.completed)
    if not ok:
        raise HTTPException(status_code=400, detail="Could not toggle task")
    return {"ok": True}


class AddTask(BaseModel):
    milestone_name: str
    task_text: str


@app.put("/api/projects/{project_id:path}/add-task")
async def add_task(project_id: str, body: AddTask):
    _, roadmap = _get_roadmap(project_id)
    ok = add_task_to_milestone(roadmap, body.milestone_name, body.task_text)
    if not ok:
        raise HTTPException(status_code=400, detail="Could not add task")
    return {"ok": True}


class GtdMove(BaseModel):
    line_index: int
    target_section: str  # next_actions | waiting_for | inbox | done


@app.put("/api/projects/{project_id:path}/gtd")
async def gtd_move(project_id: str, body: GtdMove):
    _, roadmap = _get_roadmap(project_id)
    if body.target_section == "done":
        ok = toggle_task(roadmap, body.line_index, True)
    else:
        ok = move_gtd_task(roadmap, body.line_index, body.target_section)
    if not ok:
        raise HTTPException(status_code=400, detail="Could not move task")
    return {"ok": True}


class InboxAdd(BaseModel):
    text: str
    section: str = "inbox"  # inbox | next_actions


@app.post("/api/projects/{project_id:path}/inbox")
async def add_inbox(project_id: str, body: InboxAdd):
    proj_dir, roadmap = _get_roadmap(project_id)
    ok = add_to_gtd_section(roadmap, body.section, body.text, project_name=proj_dir.name)
    if not ok:
        raise HTTPException(status_code=400, detail="Could not add to section")
    return {"ok": True}


class StatusUpdate(BaseModel):
    field: str   # current_phase | next_deadline | critical_dependency
    value: str


@app.put("/api/projects/{project_id:path}/status")
async def update_status(project_id: str, body: StatusUpdate):
    _, roadmap = _get_roadmap(project_id)
    ok = update_status_field(roadmap, body.field, body.value)
    if not ok:
        raise HTTPException(status_code=400, detail=f"Could not update field '{body.field}'")
    return {"ok": True}


class MilestoneDate(BaseModel):
    milestone_name: str
    target_date: str


@app.put("/api/projects/{project_id:path}/milestone-date")
async def set_milestone_date(project_id: str, body: MilestoneDate):
    _, roadmap = _get_roadmap(project_id)
    ok = update_milestone_target(roadmap, body.milestone_name, body.target_date)
    if not ok:
        raise HTTPException(status_code=400, detail="Could not update milestone date")
    return {"ok": True}


class DecisionAdd(BaseModel):
    date: str
    decision: str
    rationale: str


@app.post("/api/projects/{project_id:path}/decision")
async def add_decision_entry(project_id: str, body: DecisionAdd):
    _, roadmap = _get_roadmap(project_id)
    ok = add_decision(roadmap, body.date, body.decision, body.rationale)
    if not ok:
        raise HTTPException(status_code=400, detail="Could not add decision")
    return {"ok": True}


class TaskEdit(BaseModel):
    line_index: int
    new_text: str


@app.put("/api/projects/{project_id:path}/edit-task")
async def edit_task_text(project_id: str, body: TaskEdit):
    _, roadmap = _get_roadmap(project_id)
    ok = update_task_text(roadmap, body.line_index, body.new_text)
    if not ok:
        raise HTTPException(status_code=400, detail="Could not edit task")
    return {"ok": True}


# ─── Start ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"James PM — Projects dir: {BASE_PATH}")
    if not BASE_PATH.exists():
        print(f"WARNING: Projects directory not found: {BASE_PATH}")
        print("Set JAMES_PM_BASE_PATH environment variable to override.")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
