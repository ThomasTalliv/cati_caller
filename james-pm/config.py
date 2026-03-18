import os
from pathlib import Path

# Base path for the project files
# Can be overridden with JAMES_PM_BASE_PATH environment variable
DEFAULT_BASE_PATH = "/Users/thomasciliushansen/Documents/Claude/01 Projekter"

BASE_PATH = Path(os.environ.get("JAMES_PM_BASE_PATH", DEFAULT_BASE_PATH))

# Project color mapping
PROJECT_COLORS = {
    "AI Academy": "#6366f1",
    "Talliv": "#f97316",
    "Felt 64": "#8b5cf6",
    "thomascilius.dk": "#06b6d4",
    "Prism Point": "#10b981",
    "AI CATI caller": "#f43f5e",
}

DEFAULT_COLOR = "#6b7280"


def get_project_color(project_name: str) -> str:
    for key, color in PROJECT_COLORS.items():
        if key.lower() in project_name.lower() or project_name.lower() in key.lower():
            return color
    return DEFAULT_COLOR


def get_projects_dir() -> Path:
    return BASE_PATH


def get_project_dirs() -> list[Path]:
    """Return all subdirectories in the projects folder."""
    if not BASE_PATH.exists():
        return []
    dirs = []
    for item in sorted(BASE_PATH.iterdir()):
        if item.is_dir():
            dirs.append(item)
    return dirs
