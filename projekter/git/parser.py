"""
Robust ROADMAP.md parser. Handles varierende whitespace og formattering.
"""
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Task:
    text: str
    completed: bool
    line_index: int  # line index in original file


@dataclass
class Milestone:
    name: str
    target: str
    tasks: list[Task] = field(default_factory=list)
    line_index: int = 0


@dataclass
class WBSTask:
    text: str
    completed: bool
    line_index: int


@dataclass
class WBSEpic:
    name: str
    tasks: list[WBSTask] = field(default_factory=list)
    line_index: int = 0


@dataclass
class WBSMilestone:
    name: str
    epics: list[WBSEpic] = field(default_factory=list)
    line_index: int = 0


@dataclass
class DecisionEntry:
    date: str
    decision: str
    rationale: str


@dataclass
class ProjectData:
    name: str
    path: Path
    vision: str = ""
    current_phase: str = ""
    next_deadline: str = ""
    critical_dependency: str = ""
    milestones: list[Milestone] = field(default_factory=list)
    next_actions: list[Task] = field(default_factory=list)
    waiting_for: list[Task] = field(default_factory=list)
    inbox: list[str] = field(default_factory=list)
    wbs: list[WBSMilestone] = field(default_factory=list)
    decisions: list[DecisionEntry] = field(default_factory=list)
    raw_lines: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        total = sum(len(m.tasks) for m in self.milestones)
        done = sum(sum(1 for t in m.tasks if t.completed) for m in self.milestones)
        progress = round((done / total * 100) if total > 0 else 0)

        return {
            "name": self.name,
            "path": str(self.path),
            "vision": self.vision,
            "current_phase": self.current_phase,
            "next_deadline": self.next_deadline,
            "critical_dependency": self.critical_dependency,
            "milestones": [
                {
                    "name": m.name,
                    "target": m.target,
                    "tasks": [{"text": t.text, "completed": t.completed, "line_index": t.line_index} for t in m.tasks],
                    "progress": round(
                        sum(1 for t in m.tasks if t.completed) / len(m.tasks) * 100
                        if m.tasks else 0
                    ),
                    "line_index": m.line_index,
                }
                for m in self.milestones
            ],
            "next_actions": [{"text": t.text, "completed": t.completed, "line_index": t.line_index} for t in self.next_actions],
            "waiting_for": [{"text": t.text, "completed": t.completed, "line_index": t.line_index} for t in self.waiting_for],
            "inbox": self.inbox,
            "wbs": [
                {
                    "name": wm.name,
                    "epics": [
                        {
                            "name": we.name,
                            "tasks": [{"text": t.text, "completed": t.completed, "line_index": t.line_index} for t in we.tasks],
                            "line_index": we.line_index,
                        }
                        for we in wm.epics
                    ],
                    "line_index": wm.line_index,
                }
                for wm in self.wbs
            ],
            "decisions": [
                {"date": d.date, "decision": d.decision, "rationale": d.rationale}
                for d in self.decisions
            ],
            "progress": progress,
            "total_tasks": total,
            "done_tasks": done,
        }


def _parse_task_line(line: str, line_index: int) -> Optional[Task]:
    """Parse a markdown checkbox line: - [ ] text or - [x] text"""
    m = re.match(r'^\s*-\s*\[([xX ])\]\s*(.*)', line)
    if m:
        completed = m.group(1).lower() == 'x'
        text = m.group(2).strip()
        return Task(text=text, completed=completed, line_index=line_index)
    return None


def parse_roadmap(roadmap_path: Path) -> Optional[ProjectData]:
    """Parse a ROADMAP.md file into a ProjectData object."""
    if not roadmap_path.exists():
        return None

    try:
        content = roadmap_path.read_text(encoding='utf-8')
    except Exception:
        return None

    lines = content.splitlines()
    project_name = roadmap_path.parent.name

    data = ProjectData(name=project_name, path=roadmap_path.parent)
    data.raw_lines = lines

    # Determine sections by scanning through lines
    i = 0
    current_section = None
    current_milestone = None
    current_wbs_milestone = None
    current_wbs_epic = None
    in_vision = False
    in_status = False
    in_milestones = False
    in_gtd = False
    in_wbs = False
    in_decisions = False
    in_next_actions = False
    in_waiting_for = False
    in_inbox = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # H1 — project title (ignore for name, we use dir name)
        if re.match(r'^#\s+', line) and not re.match(r'^#{2,}', line):
            in_vision = False
            in_status = False
            i += 1
            continue

        # H2 sections
        if re.match(r'^##\s+', line):
            header = re.sub(r'^##\s+', '', line).strip().lower()
            in_vision = 'vision' in header
            in_status = 'status' in header
            in_milestones = 'milestone' in header
            in_gtd = 'aktiv sprint' in header or 'aktiv sprint' in header or 'sprint' in header
            in_wbs = 'work breakdown' in header or 'wbs' in header
            in_decisions = 'beslutning' in header or 'decision' in header
            in_next_actions = False
            in_waiting_for = False
            in_inbox = False
            current_milestone = None
            current_wbs_milestone = None
            current_wbs_epic = None
            i += 1
            continue

        # H3 sections
        if re.match(r'^###\s+', line):
            header = re.sub(r'^###\s+', '', line).strip()
            header_lower = header.lower()

            if in_milestones or (not in_gtd and not in_wbs and not in_decisions and not in_status):
                # Could be a milestone: ### M1: Name — Target: DATE
                m = re.match(r'^(M\d+[:\.]?\s*.+?)(?:\s*[—–-]+\s*Target:\s*(.+))?$', header, re.IGNORECASE)
                if m:
                    ms_name = m.group(1).strip()
                    ms_target = m.group(2).strip() if m.group(2) else "TBD"
                    current_milestone = Milestone(name=ms_name, target=ms_target, line_index=i)
                    data.milestones.append(current_milestone)
                    in_milestones = True
                    i += 1
                    continue

            if in_gtd:
                in_next_actions = 'next action' in header_lower or 'næste' in header_lower
                in_waiting_for = 'waiting' in header_lower or 'venter' in header_lower
                in_inbox = 'inbox' in header_lower
                i += 1
                continue

            if in_wbs:
                # H3 under WBS = milestone heading
                m = re.match(r'^(M\d+[:\.]?\s*.+)', header)
                if m:
                    wbs_ms = WBSMilestone(name=m.group(1).strip(), line_index=i)
                    data.wbs.append(wbs_ms)
                    current_wbs_milestone = wbs_ms
                    current_wbs_epic = None
                i += 1
                continue

            i += 1
            continue

        # H4 sections (WBS epics)
        if re.match(r'^####\s+', line) and in_wbs:
            header = re.sub(r'^####\s+', '', line).strip()
            if current_wbs_milestone is not None:
                epic = WBSEpic(name=header, line_index=i)
                current_wbs_milestone.epics.append(epic)
                current_wbs_epic = epic
            i += 1
            continue

        # Vision blockquote
        if in_vision and stripped.startswith('>'):
            vision_text = stripped[1:].strip()
            if data.vision:
                data.vision += ' ' + vision_text
            else:
                data.vision = vision_text
            i += 1
            continue

        # Status fields
        if in_status:
            m = re.match(r'^\*\*Nuværende fase:\*\*\s*(.*)', stripped)
            if m:
                data.current_phase = m.group(1).strip()
            m = re.match(r'^\*\*Næste deadline:\*\*\s*(.*)', stripped)
            if m:
                data.next_deadline = m.group(1).strip()
            m = re.match(r'^\*\*Kritisk afhængighed:\*\*\s*(.*)', stripped)
            if m:
                data.critical_dependency = m.group(1).strip()
            i += 1
            continue

        # Tasks in milestones
        if in_milestones and current_milestone is not None:
            task = _parse_task_line(line, i)
            if task:
                current_milestone.tasks.append(task)
            i += 1
            continue

        # GTD sections
        if in_next_actions:
            task = _parse_task_line(line, i)
            if task:
                data.next_actions.append(task)
            elif stripped and not re.match(r'^#{1,4}\s+', line):
                pass  # skip non-task lines
            i += 1
            continue

        if in_waiting_for:
            task = _parse_task_line(line, i)
            if task:
                data.waiting_for.append(task)
            i += 1
            continue

        if in_inbox:
            # Inbox items can be - text (without checkbox)
            m = re.match(r'^\s*-\s+(.*)', stripped)
            if m:
                text = m.group(1).strip()
                # Filter out checkbox lines
                if not re.match(r'^\[[ xX]\]', text):
                    data.inbox.append(text)
            i += 1
            continue

        # WBS tasks
        if in_wbs and current_wbs_epic is not None:
            task = _parse_task_line(line, i)
            if task:
                current_wbs_epic.tasks.append(task)
            i += 1
            continue

        # Decision log (markdown table)
        if in_decisions:
            # Skip header and separator rows
            if stripped.startswith('|') and not re.match(r'^\|[-\s|]+\|', stripped):
                parts = [p.strip() for p in stripped.strip('|').split('|')]
                if len(parts) >= 3 and parts[0].lower() not in ('dato', 'date'):
                    data.decisions.append(DecisionEntry(
                        date=parts[0],
                        decision=parts[1],
                        rationale=parts[2] if len(parts) > 2 else ''
                    ))
            i += 1
            continue

        i += 1

    return data


def parse_project_from_dir(project_dir: Path) -> Optional[ProjectData]:
    """Parse a project from its directory (looks for ROADMAP.md)."""
    roadmap = project_dir / "ROADMAP.md"
    if roadmap.exists():
        data = parse_roadmap(roadmap)
        if data:
            return data

    # If no ROADMAP.md, return minimal data
    return ProjectData(
        name=project_dir.name,
        path=project_dir,
    )
