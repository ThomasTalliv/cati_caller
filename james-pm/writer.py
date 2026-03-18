"""
Atomic writes back to ROADMAP.md files.
Read → modify in-memory → write entire file at once.
Creates .bak backup before first write.
"""
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


def _backup_if_needed(filepath: Path):
    """Create a .bak copy with timestamp on first write."""
    bak_dir = filepath.parent / ".backups"
    bak_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak_path = bak_dir / f"{filepath.name}.{ts}.bak"
    if not bak_path.exists():
        shutil.copy2(filepath, bak_path)


def _read_lines(filepath: Path) -> list[str]:
    return filepath.read_text(encoding='utf-8').splitlines()


def _write_lines(filepath: Path, lines: list[str]):
    _backup_if_needed(filepath)
    filepath.write_text('\n'.join(lines) + '\n', encoding='utf-8')


# ─── Task toggle ────────────────────────────────────────────────────────────

def toggle_task(roadmap_path: Path, line_index: int, completed: bool) -> bool:
    """Toggle a checkbox at line_index. Returns True on success."""
    if not roadmap_path.exists():
        return False
    lines = _read_lines(roadmap_path)
    if line_index >= len(lines):
        return False

    line = lines[line_index]
    if completed:
        lines[line_index] = re.sub(r'\[[ ]\]', '[x]', line, count=1)
    else:
        lines[line_index] = re.sub(r'\[[xX]\]', '[ ]', line, count=1)

    _write_lines(roadmap_path, lines)
    return True


# ─── Add task to milestone ───────────────────────────────────────────────────

def add_task_to_milestone(roadmap_path: Path, milestone_name: str, task_text: str) -> bool:
    """Append a new unchecked task to the specified milestone section."""
    if not roadmap_path.exists():
        return False
    lines = _read_lines(roadmap_path)

    # Find the milestone header line
    target_line = -1
    ms_pattern = re.compile(re.escape(milestone_name), re.IGNORECASE)

    for idx, line in enumerate(lines):
        if re.match(r'^###\s+', line) and ms_pattern.search(line):
            target_line = idx
            break

    if target_line == -1:
        return False

    # Find insertion point: after the last task line in this milestone
    # (before the next ### or ## header)
    insert_at = target_line + 1
    for idx in range(target_line + 1, len(lines)):
        line = lines[idx]
        if re.match(r'^#{2,3}\s+', line):
            break
        if re.match(r'^\s*-\s*\[', line):
            insert_at = idx + 1

    lines.insert(insert_at, f"- [ ] {task_text}")
    _write_lines(roadmap_path, lines)
    return True


# ─── GTD operations ─────────────────────────────────────────────────────────

def _find_gtd_section(lines: list[str], section_header: str) -> int:
    """Find the line index of a GTD subsection (### Next Actions etc)."""
    patterns = {
        'next_actions': [r'next action', r'næste'],
        'waiting_for': [r'waiting', r'venter'],
        'inbox': [r'inbox'],
    }
    pats = patterns.get(section_header, [section_header.lower()])

    for idx, line in enumerate(lines):
        if re.match(r'^###\s+', line):
            lower = line.lower()
            if any(re.search(p, lower) for p in pats):
                return idx
    return -1


def add_to_gtd_section(roadmap_path: Path, section: str, text: str, project_name: str = "") -> bool:
    """Add a new item to a GTD section (next_actions, waiting_for, inbox)."""
    if not roadmap_path.exists():
        return False
    lines = _read_lines(roadmap_path)
    section_idx = _find_gtd_section(lines, section)

    if section_idx == -1:
        # Section not found — append it to the Aktiv Sprint section or end of file
        sprint_idx = -1
        for idx, line in enumerate(lines):
            if re.match(r'^##\s+', line) and ('sprint' in line.lower() or 'aktiv' in line.lower()):
                sprint_idx = idx
                break

        if sprint_idx == -1:
            # Just append at end
            section_headers = {
                'next_actions': '### Next Actions (GTD)',
                'waiting_for': '### Waiting For',
                'inbox': '### Inbox — Fangede idéer',
            }
            header = section_headers.get(section, f"### {section}")
            lines.append('')
            lines.append(header)
            section_idx = len(lines) - 1
        else:
            section_headers = {
                'next_actions': '### Next Actions (GTD)',
                'waiting_for': '### Waiting For',
                'inbox': '### Inbox — Fangede idéer',
            }
            header = section_headers.get(section, f"### {section}")
            lines.insert(sprint_idx + 1, header)
            lines.insert(sprint_idx + 2, '')
            section_idx = sprint_idx + 1

    # Find insertion point (after existing items in this section)
    insert_at = section_idx + 1
    for idx in range(section_idx + 1, len(lines)):
        line = lines[idx]
        if re.match(r'^#{2,3}\s+', line):
            break
        if re.match(r'^\s*-\s', line):
            insert_at = idx + 1

    if section == 'next_actions':
        proj_suffix = f" → Projekt: {project_name} | Milestone: ?" if project_name else ""
        new_line = f"- [ ] **{text}**{proj_suffix}"
    elif section == 'inbox':
        new_line = f"- {text}"
    else:
        new_line = f"- [ ] {text}"

    lines.insert(insert_at, new_line)
    _write_lines(roadmap_path, lines)
    return True


def move_gtd_task(roadmap_path: Path, line_index: int, target_section: str) -> bool:
    """Move a GTD task from one section to another."""
    if not roadmap_path.exists():
        return False
    lines = _read_lines(roadmap_path)
    if line_index >= len(lines):
        return False

    task_line = lines[line_index]
    # Remove original
    lines.pop(line_index)
    _write_lines(roadmap_path, lines)

    # Re-read and add to new section
    lines = _read_lines(roadmap_path)
    section_idx = _find_gtd_section(lines, target_section)

    if section_idx == -1:
        lines.append(task_line)
    else:
        insert_at = section_idx + 1
        for idx in range(section_idx + 1, len(lines)):
            line = lines[idx]
            if re.match(r'^#{2,3}\s+', line):
                break
            if re.match(r'^\s*-\s', line):
                insert_at = idx + 1
        lines.insert(insert_at, task_line)

    _write_lines(roadmap_path, lines)
    return True


# ─── Status fields ────────────────────────────────────────────────────────────

def update_status_field(roadmap_path: Path, field: str, value: str) -> bool:
    """Update Nuværende fase, Næste deadline, or Kritisk afhængighed."""
    if not roadmap_path.exists():
        return False
    lines = _read_lines(roadmap_path)

    field_patterns = {
        'current_phase': r'(\*\*Nuværende fase:\*\*\s*)(.*)',
        'next_deadline': r'(\*\*Næste deadline:\*\*\s*)(.*)',
        'critical_dependency': r'(\*\*Kritisk afhængighed:\*\*\s*)(.*)',
    }

    pattern = field_patterns.get(field)
    if not pattern:
        return False

    for idx, line in enumerate(lines):
        m = re.match(pattern, line.strip())
        if m:
            lines[idx] = f"{m.group(1)}{value}"
            _write_lines(roadmap_path, lines)
            return True

    return False


# ─── Milestone target date ────────────────────────────────────────────────────

def update_milestone_target(roadmap_path: Path, milestone_name: str, target_date: str) -> bool:
    """Update the Target date of a milestone header."""
    if not roadmap_path.exists():
        return False
    lines = _read_lines(roadmap_path)

    ms_pattern = re.compile(re.escape(milestone_name), re.IGNORECASE)
    for idx, line in enumerate(lines):
        if re.match(r'^###\s+', line) and ms_pattern.search(line):
            # Replace or add Target date
            if 'Target:' in line or 'target:' in line:
                lines[idx] = re.sub(r'(Target:\s*)[\w\d\-/TBD]+', f'Target: {target_date}', line)
            else:
                lines[idx] = line.rstrip() + f' — Target: {target_date}'
            _write_lines(roadmap_path, lines)
            return True

    return False


# ─── Decision log ─────────────────────────────────────────────────────────────

def add_decision(roadmap_path: Path, date: str, decision: str, rationale: str) -> bool:
    """Append a row to the Beslutningslog table."""
    if not roadmap_path.exists():
        return False
    lines = _read_lines(roadmap_path)

    # Find Beslutningslog section
    beslut_idx = -1
    for idx, line in enumerate(lines):
        if re.match(r'^##\s+', line) and ('beslutning' in line.lower() or 'decision' in line.lower()):
            beslut_idx = idx
            break

    if beslut_idx == -1:
        # Append section at end
        lines.append('')
        lines.append('## Beslutningslog')
        lines.append('')
        lines.append('| Dato | Beslutning | Rationale |')
        lines.append('|------|------------|-----------|')
        beslut_idx = len(lines) - 3

    # Find insertion point (after last table row or after separator)
    insert_at = len(lines)
    in_section = False
    for idx in range(beslut_idx, len(lines)):
        line = lines[idx]
        if idx > beslut_idx and re.match(r'^##\s+', line):
            insert_at = idx
            break
        if line.strip().startswith('|'):
            insert_at = idx + 1
            in_section = True

    # If no table found in section, create it
    if not in_section:
        lines.insert(beslut_idx + 1, '')
        lines.insert(beslut_idx + 2, '| Dato | Beslutning | Rationale |')
        lines.insert(beslut_idx + 3, '|------|------------|-----------|')
        insert_at = beslut_idx + 4

    new_row = f"| {date} | {decision} | {rationale} |"
    lines.insert(insert_at, new_row)
    _write_lines(roadmap_path, lines)
    return True


# ─── Inline task text edit ────────────────────────────────────────────────────

def update_task_text(roadmap_path: Path, line_index: int, new_text: str) -> bool:
    """Update the text of a task at line_index, preserving the checkbox state."""
    if not roadmap_path.exists():
        return False
    lines = _read_lines(roadmap_path)
    if line_index >= len(lines):
        return False

    line = lines[line_index]
    m = re.match(r'^(\s*-\s*\[[ xX]\]\s*)(.*)', line)
    if m:
        lines[line_index] = m.group(1) + new_text
        _write_lines(roadmap_path, lines)
        return True
    return False
